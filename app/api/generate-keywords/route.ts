import { NextRequest, NextResponse } from 'next/server';
import OpenAI from 'openai';

// Lazy initialization to avoid build-time errors
function getOpenAIClient() {
  if (!process.env.OPENAI_API_KEY) {
    throw new Error('OPENAI_API_KEY is not configured');
  }
  return new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
  });
}

// 기본 키워드 생성 (GPT 없이)
function generateBasicKeywords(productName: string, category?: string): string[] {
  const keywords: string[] = [];

  // 상품명에서 키워드 추출
  const words = productName.replace(/[\/\-_]/g, ' ').split(/\s+/).filter(w => w.length > 1);
  keywords.push(...words);

  // 상품명 전체도 추가
  keywords.push(productName);

  // 카테고리에서 키워드 추출
  if (category) {
    const categoryParts = category.split('>').map(p => p.trim()).filter(p => p.length > 0);
    keywords.push(...categoryParts);
  }

  // 조합 키워드 생성
  if (words.length >= 2) {
    for (let i = 0; i < words.length - 1; i++) {
      keywords.push(`${words[i]} ${words[i + 1]}`);
    }
  }

  // 중복 제거
  return [...new Set(keywords)];
}

export async function POST(request: NextRequest) {
  try {
    const { product_name, category, count = 30 } = await request.json();

    if (!product_name) {
      return NextResponse.json(
        { success: false, error: '상품명이 필요합니다.' },
        { status: 400 }
      );
    }

    // OpenAI API 키 확인
    if (!process.env.OPENAI_API_KEY) {
      console.warn('OpenAI API 키가 없어 기본 키워드를 생성합니다.');
      const basicKeywords = generateBasicKeywords(product_name, category);
      return NextResponse.json({
        success: true,
        keywords: basicKeywords.slice(0, count),
        source: 'basic'
      });
    }

    try {
      const openai = getOpenAIClient();

      // 카테고리 정보 포함
      let categoryHint = '';
      if (category) {
        categoryHint = `\n카테고리: ${category}`;
      }

      // GPT에게 키워드 생성 요청
      const prompt = `다음 상품에 대한 검색 키워드를 ${Math.min(count, 40)}개 생성해주세요.
검색 키워드는 해당 상품을 고객이 검색할 때 사용할 만한 단어들입니다.

상품명: ${product_name}${categoryHint}

요구사항:
1. 상품명에 포함된 단어들을 활용
2. 유사어, 관련어 포함
3. 브랜드명, 제품 특성, 용도 등 포함
4. 오픈마켓에서 실제로 검색할 만한 키워드
5. 한글 키워드 위주 (필요시 영문 포함)

JSON 배열 형식으로만 응답해주세요. 예: ["키워드1", "키워드2", ...]`;

      const completion = await openai.chat.completions.create({
        model: 'gpt-4o-mini',
        messages: [
          {
            role: 'user',
            content: prompt,
          },
        ],
        temperature: 0.7,
        max_tokens: 1000,
      });

      const content = completion.choices[0]?.message?.content || '';

      // JSON 파싱
      const jsonMatch = content.match(/\[[\s\S]*\]/);
      if (jsonMatch) {
        const keywords = JSON.parse(jsonMatch[0]) as string[];
        return NextResponse.json({
          success: true,
          keywords: keywords.slice(0, 40),
          source: 'gpt'
        });
      }

      // 파싱 실패 시 기본 키워드
      const basicKeywords = generateBasicKeywords(product_name, category);
      return NextResponse.json({
        success: true,
        keywords: basicKeywords.slice(0, count),
        source: 'basic_fallback'
      });

    } catch (openaiError: any) {
      console.error('OpenAI API 오류:', openaiError);

      // OpenAI 오류 시 기본 키워드
      const basicKeywords = generateBasicKeywords(product_name, category);
      return NextResponse.json({
        success: true,
        keywords: basicKeywords.slice(0, count),
        source: 'basic_fallback',
        error: openaiError.message
      });
    }

  } catch (error: any) {
    console.error('키워드 생성 오류:', error);
    return NextResponse.json(
      { success: false, error: '키워드 생성 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}
