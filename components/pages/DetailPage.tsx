'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { ArrowLeft, Download, Sparkles, CheckCircle, ShoppingCart, RefreshCw, Search, ExternalLink, DollarSign, Plus, Tag, AlertCircle, Upload } from 'lucide-react';
import { templates, getTemplateIcon } from '@/lib/templates';
import { imageService } from '@/lib/imageService';
import type { Category, TemplateType } from '@/types';
import * as htmlToImage from 'html-to-image';
import DailyTemplate from '@/components/templates/DailyTemplate';
import FoodTemplate from '@/components/templates/FoodTemplate';
import ElectronicsTemplate from '@/components/templates/ElectronicsTemplate';
import ProcessedFoodTemplate from '@/components/templates/ProcessedFoodTemplate';
import HygieneTemplate from '@/components/templates/HygieneTemplate';
import StationeryTemplate from '@/components/templates/StationeryTemplate';
import PreUploadedTemplate from '@/components/templates/PreUploadedTemplate';
import TextStyleEditor from '@/components/templates/TextStyleEditor';
import PropertiesPanel from '@/components/ui/PropertiesPanel';
import KeywordEditor from '@/components/ui/KeywordEditor';
import { API_BASE_URL, categoriesApi } from '@/lib/api';

type Screen = 'category-selection' | 'product-input' | 'generating' | 'result';

interface GeneratedContent {
  productName: string;
  [key: string]: any;
}

export default function DetailPage() {
  const [screen, setScreen] = useState<Screen>('category-selection');
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateType | null>(null);
  const [category, setCategory] = useState<Category>({ level1: '', level2: '', level3: '', level4: '' });

  // 동적 카테고리 구조 state 추가
  const [categoryStructure, setCategoryStructure] = useState<Record<string, any>>({});
  const [isCategoryLoading, setIsCategoryLoading] = useState(true);

  const [productName, setProductName] = useState('');
  const [productUrl, setProductUrl] = useState('');
  const [isExtractingUrl, setIsExtractingUrl] = useState(false);
  const [extractedThumbnail, setExtractedThumbnail] = useState<string>('');
  const [sourcingPrice, setSourcingPrice] = useState<number | null>(null); // 소싱가 (원가)
  const [sellingPrice, setSellingPrice] = useState<number | null>(null); // 판매가 (30% 마진)
  const [detectedSource, setDetectedSource] = useState<string>(''); // 감지된 마켓
  const [manualInputRequired, setManualInputRequired] = useState(false); // 수동 입력 필요 여부
  const [manualInputMessage, setManualInputMessage] = useState(''); // 수동 입력 안내 메시지
  const [inputType, setInputType] = useState<'auto' | 'manual'>('auto'); // 입력 방식
  const [generatedContent, setGeneratedContent] = useState<GeneratedContent | null>(null);
  const [uploadedImages, setUploadedImages] = useState<Record<string, string>>({});
  const [editingField, setEditingField] = useState<string | null>(null);
  const [editingValue, setEditingValue] = useState('');
  const [editingImage, setEditingImage] = useState<string | null>(null);
  const [imageStyleSettings, setImageStyleSettings] = useState<Record<string, any>>({});
  const [editingTextStyle, setEditingTextStyle] = useState<string | null>(null);
  const [textStyles, setTextStyles] = useState<Record<string, { fontSize?: string; color?: string; fontWeight?: string; textAlign?: string }>>({});
  const [selectedElement, setSelectedElement] = useState<{ type: 'text' | 'image' | null; field: string | null }>({ type: null, field: null });
  const [showError, setShowError] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [isSaving, setIsSaving] = useState(false);
  const [additionalImageSlots, setAdditionalImageSlots] = useState<number>(0);
  const [isAddingToMonitoring, setIsAddingToMonitoring] = useState(false);
  const [showAddProductModal, setShowAddProductModal] = useState(false);
  const [imageSizes, setImageSizes] = useState<Record<string, number>>({});
  const [imagePositions, setImagePositions] = useState<Record<string, { x: number; y: number }>>({});
  const [imageAlignments, setImageAlignments] = useState<Record<string, 'left' | 'center' | 'right'>>({});
  const [containerWidths, setContainerWidths] = useState<Record<string, number>>({}); // 컨테이너 가로 크기 (%)
  const [hiddenSections, setHiddenSections] = useState<Record<string, boolean>>({}); // 숨겨진(삭제된) 섹션
  const [isUploadingDetailPage, setIsUploadingDetailPage] = useState(false); // 상세페이지 이미지 업로드 중
  const templateRef = useRef<HTMLDivElement>(null);
  const detailPageInputRef = useRef<HTMLInputElement>(null);

  // 카테고리 구조 로드
  useEffect(() => {
    const loadCategoryStructure = async (useCache = true) => {
      try {
        setIsCategoryLoading(true);
        const data = await categoriesApi.getStructure(useCache);
        if (data.success && data.structure) {
          setCategoryStructure(data.structure);
          console.log('✅ 카테고리 구조 로드 완료:', Object.keys(data.structure).length, '개 대분류');
        } else {
          console.error('카테고리 구조 로드 실패');
          // 폴백: 빈 객체 사용
          setCategoryStructure({});
        }
      } catch (error) {
        console.error('카테고리 구조 로드 오류:', error);
        setCategoryStructure({});
      } finally {
        setIsCategoryLoading(false);
      }
    };

    // 초기 로드
    loadCategoryStructure(true);

    // 페이지가 다시 보일 때 (다른 탭에서 돌아올 때) 재로드
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        console.log('🔄 페이지 활성화 감지 - 카테고리 재로드');
        loadCategoryStructure(false); // 캐시 무시하고 재로드
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  // 외부 클릭 시 편집 모드 해제
  const handleOutsideClick = (e: React.MouseEvent) => {
    const target = e.target as HTMLElement;
    // 편집 가능한 요소, 편집 컨테이너, 또는 속성 패널 내부 클릭은 무시
    if (
      !target.closest('[data-editable]') &&
      !target.closest('.editable-container') &&
      !target.closest('.properties-panel')
    ) {
      setEditingField(null);
      setEditingImage(null);
      setEditingTextStyle(null);
      setSelectedElement({ type: null, field: null });
    }
  };

  // 이미지 정렬 변경
  const handleImageAlignment = (imageKey: string, alignment: 'left' | 'center' | 'right') => {
    setImageAlignments(prev => ({ ...prev, [imageKey]: alignment }));
  };

  // 컨테이너 가로 크기 변경 (+ 버튼 이미지용)
  const handleContainerWidthChange = (imageKey: string, width: number) => {
    setContainerWidths(prev => ({ ...prev, [imageKey]: width }));
  };

  const handleSectionDelete = (sectionKey: string) => {
    if (window.confirm('이 섹션을 삭제하시겠습니까?')) {
      setHiddenSections(prev => ({ ...prev, [sectionKey]: true }));
    }
  };

  const fileInputRefs = useRef<Record<string, HTMLInputElement | null>>({});

  const level1Options = Object.keys(categoryStructure);
  const level2Options = category.level1 ? Object.keys((categoryStructure as any)[category.level1] || {}) : [];
  const level3Options = category.level1 && category.level2 ? Object.keys((categoryStructure as any)[category.level1]?.[category.level2] || {}) : [];
  const level4Options = category.level1 && category.level2 && category.level3 ? (categoryStructure as any)[category.level1]?.[category.level2]?.[category.level3] || [] : [];

  const handleCategoryChange = (level: keyof Category, value: string) => {
    setCategory(prev => {
      const updated = { ...prev, [level]: value };
      if (level === 'level1') {
        updated.level2 = '';
        updated.level3 = '';
        updated.level4 = '';
      } else if (level === 'level2') {
        updated.level3 = '';
        updated.level4 = '';
      } else if (level === 'level3') {
        updated.level4 = '';
      }
      return updated;
    });
  };

  const handleTemplateSelect = (templateKey: TemplateType) => {
    if (!category.level1 || !category.level2 || !category.level3 || !category.level4) {
      setShowError(true);
      return;
    }
    setSelectedTemplate(templateKey);
    setShowError(false);
    // 이미지 로딩은 생성 버튼 클릭 시 수행
    setScreen('product-input');
  };

  const extractUrlInfo = async () => {
    if (!productUrl) {
      alert('URL을 입력해주세요.');
      return;
    }

    setIsExtractingUrl(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/monitor/extract-url-info`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_url: productUrl }),
      });

      if (!response.ok) {
        throw new Error('URL 정보 추출 실패');
      }

      const result = await response.json();

      // 도매꾹 등 수동 입력 필요한 경우
      if (result.manual_input_required) {
        setManualInputRequired(true);
        setManualInputMessage(result.message || '가격 정보를 직접 입력해주세요.');
        setInputType('manual');

        // 상품명과 썸네일은 자동 추출된 경우 설정
        if (result.product_name) {
          setProductName(result.product_name);
        }
        if (result.source) {
          setDetectedSource(result.source.toUpperCase());
        }

        // 썸네일 처리
        if (result.thumbnail) {
          const finalThumbnailUrl = result.thumbnail;
          try {
            const saveResponse = await fetch(`${API_BASE_URL}/api/monitor/save-thumbnail`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                image_url: finalThumbnailUrl,
                product_name: result.product_name || '상품'
              }),
            });

            if (saveResponse.ok) {
              const saveResult = await saveResponse.json();
              if (saveResult.success && saveResult.thumbnail_path) {
                setExtractedThumbnail(saveResult.thumbnail_path);
              } else {
                setExtractedThumbnail(finalThumbnailUrl);
              }
            } else {
              setExtractedThumbnail(finalThumbnailUrl);
            }
          } catch (uploadError) {
            console.error('썸네일 업로드 실패:', uploadError);
            setExtractedThumbnail(finalThumbnailUrl);
          }
        }

        return; // 여기서 종료
      }

      // 일반적인 자동 추출 케이스
      if (result.success && result.data) {
        setManualInputRequired(false);
        setInputType('auto');

        const { product_name, current_price, source, thumbnail_url } = result.data;

        // 상품명 설정
        if (product_name && product_name !== '자동 감지 실패') {
          setProductName(product_name);
        } else {
          alert('상품명을 자동으로 감지할 수 없습니다. 직접 입력해주세요.');
        }

        // 가격 설정 및 30% 마진 계산
        if (current_price && current_price > 0) {
          setSourcingPrice(current_price);
          const calculatedSellingPrice = Math.ceil(current_price * 1.3); // 30% 마진
          setSellingPrice(calculatedSellingPrice);
        }

        // 소스 설정
        if (source) {
          setDetectedSource(source.toUpperCase());
        }

        // 썸네일 처리: extract-url-info에서 받은 thumbnail_url 우선 사용
        let finalThumbnailUrl = thumbnail_url;

        // thumbnail_url이 없으면 extract-thumbnail 호출 (폴백)
        if (!finalThumbnailUrl) {
          try {
            const thumbnailResponse = await fetch(`${API_BASE_URL}/api/monitor/extract-thumbnail`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ product_url: productUrl }),
            });

            if (thumbnailResponse.ok) {
              const thumbnailResult = await thumbnailResponse.json();
              if (thumbnailResult.success && thumbnailResult.thumbnail_url) {
                finalThumbnailUrl = thumbnailResult.thumbnail_url;
              }
            }
          } catch (thumbnailError) {
            console.error('썸네일 추출 폴백 실패:', thumbnailError);
          }
        }

        // 썸네일 URL이 있으면 Supabase에 업로드
        if (finalThumbnailUrl) {
          try {
            const saveResponse = await fetch(`${API_BASE_URL}/api/monitor/save-thumbnail`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                image_url: finalThumbnailUrl,
                product_name: product_name || '상품'
              }),
            });

            if (saveResponse.ok) {
              const saveResult = await saveResponse.json();
              if (saveResult.success && saveResult.thumbnail_path) {
                // Supabase URL 사용
                setExtractedThumbnail(saveResult.thumbnail_path);
              } else {
                // Supabase 업로드 실패 시 원본 URL 사용
                setExtractedThumbnail(finalThumbnailUrl);
              }
            } else {
              // 업로드 실패 시 원본 URL 사용
              setExtractedThumbnail(finalThumbnailUrl);
            }
          } catch (uploadError) {
            console.error('썸네일 Supabase 업로드 실패:', uploadError);
            // 업로드 실패 시 원본 URL 사용
            setExtractedThumbnail(finalThumbnailUrl);
          }
        }
      }
    } catch (error) {
      console.error('URL 정보 추출 오류:', error);
      alert('URL 정보 추출에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setIsExtractingUrl(false);
    }
  };

  const callOpenAI = async (prompt: string, maxRetries = 3): Promise<any> => {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        console.log(`🤖 OpenAI API 호출 시도 ${attempt}/${maxRetries}`);
        if (attempt > 1) {
          await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt - 1) * 1000));
        }

        const response = await fetch('/api/generate-content', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt }),
        });

        if (response.status === 429) {
          console.warn(`⚠️ OpenAI API 요청 한도 초과 (429) - 시도 ${attempt}/${maxRetries}`);
          if (attempt === maxRetries) {
            throw new Error('OpenAI API 요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요.');
          }
          continue;
        }

        if (!response.ok) {
          throw new Error(`OpenAI API Error: ${response.status}`);
        }

        const data = await response.json();
        const content = data.choices?.[0]?.message?.content ?? '';
        if (!content) {
          throw new Error('OpenAI 응답이 비어있습니다.');
        }

        console.log('✅ OpenAI API 호출 성공');
        const jsonMatch = content.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
          return JSON.parse(jsonMatch[0]);
        }
        return null;
      } catch (error) {
        console.error(`❌ OpenAI API 호출 실패 (시도 ${attempt}/${maxRetries}):`, error);
        if (attempt === maxRetries) {
          throw error;
        }
      }
    }
  };

  const generateDailyContent = async () => {
    const prompt = `당신은 한국의 전문 생필품 쇼핑몰 마케터 및 상세페이지 40년차 전문가입니다.

**중요한 규칙:**
1. 모든 텍스트는 반드시 순수한 한국어(한글)로만 작성
2. 영어 단어 사용 금지
3. 한자 사용 절대 금지
4. 숫자는 아라비아 숫자 사용 가능

상품명: "${productName}"

JSON 객체를 생성:
{
"mainCopy1": "한줄 후킹 문구",
"hooking1": "후킹단어 (10자 이내)",
"hooking2": "후킹단어 (10자 이내)",
"hooking3": "후킹단어 (10자 이내)",
"hookingTitle2": "장점 제목",
"hookingSentence": "부연설명 50자",
"tag1": "장점 태그",
"tag2": "장점 태그",
"tag3": "장점 태그",
"tag4": "장점 태그",
"tag5": "장점 태그",
"tag6": "장점 태그",
"reviewSectionTitle": "리뷰 섹션 제목",
"reviewSectionSubtitle": "리뷰 섹션 부제목",
"satisfactionLabel": "만족도 라벨",
"review1": "고객 후기 3줄 이상",
"review2": "고객 후기 3줄 이상",
"review3": "고객 후기 3줄 이상",
"hookingTitle3": "장점 제목",
"hookingSentence3": "부연설명 50자",
"productGuideLabel": "상품안내 라벨",
"point1Description": "특징 설명 300자",
"point2Description": "특징 설명 300자",
"point3Description": "특징 설명 300자",
"point4Description": "특징 설명 300자",
"productInfoLabel": "상품정보 라벨",
"cautionLabel": "주의사항 라벨",
"cautions": "이 상품을 사용할 때 주의해야 할 점들을 상세히 작성. 보관방법, 사용시 주의점, 부작용 가능성, 알레르기 유발 성분, 사용 금지 대상 등을 포함하여 300자 이상 작성"
}`;

    try {
      const result = await callOpenAI(prompt);
      if (!result) throw new Error('AI 응답 파싱 실패');
      return { productName, ...result };
    } catch (error) {
      console.error('Content generation failed:', error);
      return {
        productName,
        mainCopy1: "일상을 더욱 편리하게 만드는 필수템",
        hooking1: "뛰어난품질",
        hooking2: "합리적가격",
        hooking3: "편리함",
        hookingTitle2: "매일 사용하는 생필품, 품질이 중요합니다",
        hookingSentence: "까다로운 품질 기준을 통과한 믿을 수 있는 제품",
        tag1: "품질", tag2: "가성비", tag3: "편리함", tag4: "안전성", tag5: "내구성", tag6: "실용성",
        reviewSectionTitle: "믿고쓰는 생필품!",
        reviewSectionSubtitle: "추천할 수 밖에 없는 이유!",
        satisfactionLabel: "고객만족도",
        review1: "품질이 정말 좋아요! 매일 사용하는 제품이라 걱정했는데 기대 이상입니다.",
        review2: "처음엔 반신반의했는데 써보니까 정말 대박이에요!",
        review3: "생필품은 품질이 제일 중요한데 이 제품은 정말 믿고 쓸 수 있어요.",
        reviewer1Name: "ksdfda****",
        reviewer2Name: "Wah5dr****",
        reviewer3Name: "Qhd3gh****",
        hookingTitle3: "믿을 수 있는 품질",
        hookingSentence3: "엄격한 품질 관리를 통과한 안심 제품",
        productGuideLabel: "상품안내",
        point1Description: "엄선된 원료와 까다로운 품질 관리를 통해 최고의 품질을 보장합니다.",
        point2Description: "합리적인 가격으로 최고의 가치를 제공합니다.",
        point3Description: "사용법이 간단하고 편리하여 누구나 쉽게 사용할 수 있습니다.",
        point4Description: "친환경적인 소재를 사용하여 환경을 생각하는 제품입니다.",
        productInfoLabel: "상품정보",
        cautionLabel: "주의사항",
        cautions: "• 직사광선을 피하고 서늘하고 건조한 곳에 보관해주세요.\n• 개봉 후에는 밀봉하여 보관하시고 가능한 빨리 사용해주세요.\n• 본 제품은 사용 전 사용설명서를 반드시 읽어보시기 바랍니다.\n• 피부에 이상이 생길 경우 사용을 중단하고 전문의와 상담하세요.\n• 어린이 손이 닿지 않는 곳에 보관해주세요."
      };
    }
  };

  const generateFoodContent = async () => {
    const prompt = `당신은 한국의 전문 식품 쇼핑몰 마케터입니다. 순수한 한국어로만 작성하세요.

상품명: "${productName}"

다음 JSON 형식으로 작성하세요. 각 필드는 실제 사용될 텍스트만 작성하고, 설명이나 예시는 포함하지 마세요:
{
"subtitle": "파란 배지 문구",
"badgeTop": "100%",
"badgeBottom": "정품",
"coreMessage1": "중간 섹션 제목",
"tag1": "#태그1",
"tag2": "#태그2",
"tag3": "#태그3",
"reviewSectionTitle": "리뷰 섹션 제목 (짧게)",
"reviewSectionSubtitle": "리뷰 섹션 부제목",
"review1": "고객 후기 2-3줄",
"review2": "고객 후기 2-3줄",
"review3": "고객 후기 2-3줄",
"productInfoLabel": "상품정보",
"cautionContent": "식품 보관방법, 유통기한 확인사항, 알레르기 유발 성분(대두, 밀, 우유, 계란 등), 섭취 시 주의사항을 포함하여 150자 이상 작성"
}`;

    try {
      const result = await callOpenAI(prompt);
      if (!result) throw new Error('AI 응답 파싱 실패');
      return { productName, badgeTop: "100%", badgeBottom: "정품", ...result };
    } catch (error) {
      return {
        productName,
        subtitle: `${productName}으로 입맛부터 완성하세요`,
        badgeTop: "100%",
        badgeBottom: "정품",
        coreMessage1: `맛과 영양을 모두 갖춘 ${productName}`,
        tag1: "#간편식",
        tag2: "#소시지",
        tag3: "#영양만점",
        reviewSectionTitle: "실제 구매자들의",
        reviewSectionSubtitle: "BEST REVIEW",
        review1: "품질이 정말 뛰어나요! 맛도 영양도 100점만점에 100점입니다. 매일 100개씩만 판매한다니 다시 사야겠어요.",
        review2: "맛이 기대 이상이에요! 요리 초보인 저도 쉽게 만들 수 있었어요. 가족들이 정말 좋아해요.",
        review3: "아이가 정말 좋아해요! 품질은 최상이면서도 가격은 저렴하니 주방에서 못빼겠어요.",
        reviewer1Name: "ksdfda****",
        reviewer2Name: "Wah5dr****",
        reviewer3Name: "Qhd3gh****",
        productInfoLabel: "상품 정보",
        cautionContent: "• 상품 수령 후 제품명과 수량을 꼭 확인해주세요.\n• 냉동/냉장 보관이 필요한 제품은 즉시 적정 온도에 보관하세요.\n• 유통기한을 확인하시고 기한 내 섭취해주세요.\n• 알레르기 유발 성분(대두, 밀, 우유 등)이 포함될 수 있으니 성분표를 확인하세요."
      };
    }
  };

  const generateElectronicsContent = async () => {
    const prompt = `당신은 전자제품 전문 마케터입니다. 순수한 한국어로만 작성하세요.

상품명: "${productName}"

JSON 형식으로 작성하세요:
{
"introSubtitle": "영문 슬로건 (예: PREMIUM TECH)",
"introTitle": "메인 타이틀 2줄",
"introDescription": "제품 소개 한 문장",
"feature1Title": "기능1 제목 2줄",
"feature1Description": "기능1 설명 50자",
"feature2Badge": "영문 배지 텍스트",
"feature2Title": "기능2 제목",
"feature2Description": "기능2 설명 40자",
"feature2Card1Title": "모드1 이름",
"feature2Card1Desc": "모드1 설명 20자",
"feature2Card2Title": "모드2 이름",
"feature2Card2Desc": "모드2 설명 20자",
"feature3Title": "기능3 제목 2줄",
"feature3Description": "기능3 설명 50자",
"feature3Stat1Value": "수치1 (예: 254g)",
"feature3Stat1Label": "수치1 라벨",
"feature3Stat2Value": "수치2 (예: Soft)",
"feature3Stat2Label": "수치2 라벨",
"feature4Card1Title": "부가기능1 제목",
"feature4Card1Desc": "부가기능1 설명 40자",
"feature4Card2Title": "부가기능2 제목",
"feature4Card2Desc": "부가기능2 설명 40자",
"feature4BatteryValue": "배터리 수치 (예: 30H)",
"feature5Title": "구성품 제목"
}`;

    try {
      const result = await callOpenAI(prompt);
      if (!result) throw new Error('AI 응답 파싱 실패');
      return { productName, ...result };
    } catch (error) {
      return { productName, introSubtitle: "PREMIUM TECHNOLOGY", introTitle: "기술의 혁신으로\n일상을 바꾸다", introDescription: "최첨단 기술이 담긴 프리미엄 제품을 경험하세요.", feature1Title: "차원이 다른\n성능의 차이", feature1Description: "최신 기술을 적용하여 더욱 향상된 성능을 제공합니다.", feature2Badge: "SMART TECHNOLOGY", feature2Title: "스마트한 기능", feature2Description: "편리한 사용성을 위한 다양한 스마트 기능을 갖추었습니다.", feature2Card1Title: "기본 모드", feature2Card1Desc: "일상적인 사용에 최적화", feature2Card2Title: "고급 모드", feature2Card2Desc: "더 강력한 성능이 필요할 때", feature3Title: "편안한 사용감으로\n오래 써도 부담 없이", feature3Description: "인체공학적 설계로 장시간 사용해도 편안합니다.", feature3Stat1Value: "Light", feature3Stat1Label: "가벼운 무게", feature3Stat2Value: "Soft", feature3Stat2Label: "부드러운 소재", feature4Card1Title: "빠른 충전", feature4Card1Desc: "급속 충전 기술로 짧은 시간에 충전이 완료됩니다.", feature4Card2Title: "긴 사용시간", feature4Card2Desc: "한 번 충전으로 오랫동안 사용할 수 있습니다.", feature4BatteryValue: "24H", feature5Title: "구성품 (In the Box)" };
    }
  };

  const generateProcessedFoodContent = async () => {
    const prompt = `당신은 가공식품 전문 마케터입니다. 순수한 한국어로만 작성하세요.

상품명: "${productName}"

JSON 형식으로 작성하세요:
{
"introSubtitle": "영문 슬로건 (예: PREMIUM RECIPE)",
"introTitle": "메인 타이틀 2줄",
"introDescription": "제품 소개 2문장",
"feature1Title": "재료 특징 제목 2줄",
"feature1Description": "재료 설명 60자",
"feature1Stat1Value": "수치1 (예: Fresh)",
"feature1Stat1Label": "수치1 라벨",
"feature1Stat2Value": "수치2 (예: Clean)",
"feature1Stat2Label": "수치2 라벨",
"feature2Badge": "영문 배지 텍스트",
"feature2Title": "맛 특징 제목 2줄",
"feature2Description": "맛 설명 2문장",
"feature2HighlightText": "강조 문구 15자",
"feature3Title": "조리법 제목 2줄",
"feature3Description": "조리법 설명 2문장",
"feature3Method1Title": "조리방법1 제목",
"feature3Method1Desc": "조리방법1 설명 30자",
"feature3Method2Title": "조리방법2 제목",
"feature3Method2Desc": "조리방법2 설명 30자"
}`;

    try {
      const result = await callOpenAI(prompt);
      if (!result) throw new Error('AI 응답 파싱 실패');
      return { productName, ...result };
    } catch (error) {
      return { productName, introSubtitle: "PREMIUM RECIPE", introTitle: "집에서 즐기는\n완벽한 한 끼", introDescription: "엄선된 재료와 쉐프의 비법 레시피로 완성했습니다.\n복잡한 준비 없이, 데우기만 하면 근사한 요리가 됩니다.", feature1Title: "타협하지 않는\n신선한 원재료", feature1Description: "맛의 기본은 좋은 재료에서 시작됩니다. 산지에서 갓 수확한 신선한 재료만을 사용합니다.", feature1Stat1Value: "Fresh", feature1Stat1Label: "당일 입고 재료", feature1Stat2Value: "Clean", feature1Stat2Label: "위생 공정", feature2Badge: "SECRET SAUCE", feature2Title: "입안 가득 퍼지는\n깊은 풍미의 비결", feature2Description: "수많은 테스트 끝에 완성된 황금 비율.\n자극적인 맛 대신, 재료와 어우러지는 깊은 감칠맛을 냅니다.", feature2HighlightText: "재구매율 1위의 검증된 맛", feature3Title: "바쁜 일상 속\n5분이면 충분합니다", feature3Description: "요리할 시간이 부족해도 걱정하지 마세요.\n라면만큼 쉽지만, 퀄리티는 레스토랑급입니다.", feature3Method1Title: "전자레인지 조리", feature3Method1Desc: "포장을 살짝 뜯은 후 약 4분간 데워주세요.", feature3Method2Title: "직화/냄비 조리", feature3Method2Desc: "내용물을 냄비나 팬에 붓고 중약불에서 조리하세요." };
    }
  };

  const generateHygieneContent = async () => {
    const prompt = `당신은 위생용품 전문 마케터입니다. 순수한 한국어로만 작성하세요.

상품명: "${productName}"

JSON 형식으로 작성하세요:
{
"introSubtitle": "영문 슬로건 (예: PURE & SAFE)",
"introTitle": "메인 타이틀 2줄",
"introDescription": "제품 소개 2문장",
"feature1Title": "소재 특징 제목 2줄",
"feature1Description": "소재 설명 60자",
"feature1Stat1Value": "수치1 (예: 100%)",
"feature1Stat1Label": "수치1 라벨",
"feature1Stat2Value": "수치2 (예: Zero)",
"feature1Stat2Label": "수치2 라벨",
"feature2Badge": "영문 배지 텍스트",
"feature2Title": "인증 특징 제목 2줄",
"feature2Description": "인증 설명 2문장",
"feature2Card1": "인증1 이름",
"feature2Card2": "인증2 이름",
"feature3Title": "기능 특징 제목 2줄",
"feature3Description": "기능 설명 2문장",
"feature3Point1Title": "포인트1 제목",
"feature3Point1Desc": "포인트1 설명 30자",
"feature3Point2Title": "포인트2 제목",
"feature3Point2Desc": "포인트2 설명 30자"
}`;

    try {
      const result = await callOpenAI(prompt);
      if (!result) throw new Error('AI 응답 파싱 실패');
      return { productName, ...result };
    } catch (error) {
      return { productName, introSubtitle: "PURE & SAFE", introTitle: "매일 닿는 피부니까\n더 순수하게, 더 안전하게", introDescription: "불필요한 성분은 빼고, 자연 유래 성분으로 채웠습니다.\n온 가족이 안심하고 사용할 수 있는 데일리 케어.", feature1Title: "피부가 먼저 느끼는\n자연 유래 소재", feature1Description: "민감한 피부에도 자극 없이 부드럽게 닿습니다. 엄격한 기준의 피부 저자극 테스트를 통과했습니다.", feature1Stat1Value: "100%", feature1Stat1Label: "천연 소재", feature1Stat2Value: "Zero", feature1Stat2Label: "유해성분 불검출", feature2Badge: "CERTIFIED QUALITY", feature2Title: "깐깐하게 검증받은\n안전한 품질", feature2Description: "국제 표준 인증 기관의 까다로운 절차를 모두 통과했습니다.", feature2Card1: "안전성 인증", feature2Card2: "품질 보증", feature3Title: "탁월한 흡수력과\n산뜻한 마무리감", feature3Description: "독자적인 레이어 구조로 흡수력은 높이고,\n사용 후 잔여물 걱정 없이 깔끔합니다.", feature3Point1Title: "통기성 & 건조", feature3Point1Desc: "우수한 통기성으로 언제나 보송보송합니다.", feature3Point2Title: "강력한 흡수", feature3Point2Desc: "한 번의 사용으로도 충분한 만족감을 드립니다." };
    }
  };

  const generateStationeryContent = async () => {
    const prompt = `당신은 문구류 전문 마케터입니다. 순수한 한국어로만 작성하세요.

상품명: "${productName}"

JSON 형식으로 작성하세요:
{
"introSubtitle": "영문 슬로건 (예: RECORD YOUR MOMENTS)",
"introTitle": "메인 타이틀 2줄",
"introDescription": "제품 소개 3문장",
"feature1Title": "품질 특징 제목 2줄",
"feature1Description": "품질 설명 60자",
"feature1Stat1Value": "수치1 (예: 120gsm)",
"feature1Stat1Label": "수치1 라벨",
"feature1Stat2Value": "수치2 (예: Acid-Free)",
"feature1Stat2Label": "수치2 라벨",
"feature2Badge": "영문 배지 텍스트",
"feature2Title": "디자인 특징 제목 2줄",
"feature2Description": "디자인 설명 3문장",
"feature2Card1": "특징1 (예: 180° Lay-flat)",
"feature2Card2": "특징2 (예: 견고한 하드커버)",
"feature3Title": "활용 특징 제목 2줄",
"feature3Description": "활용 설명 3문장",
"feature3Point1Title": "포인트1 제목",
"feature3Point1Desc": "포인트1 설명 30자",
"feature3Point2Title": "포인트2 제목",
"feature3Point2Desc": "포인트2 설명 30자"
}`;

    try {
      const result = await callOpenAI(prompt);
      if (!result) throw new Error('AI 응답 파싱 실패');
      return { productName, ...result };
    } catch (error) {
      return { productName, introSubtitle: "RECORD YOUR MOMENTS", introTitle: "생각이 머무는 곳,\n영감이 시작되는 공간", introDescription: "스쳐 지나가는 아이디어부터 소중한 하루의 기록까지.\n사각거리는 종이의 질감과 부드러운 필기감으로\n당신의 기록을 더욱 특별하게 만들어보세요.", feature1Title: "비침 없이 완벽한\n프리미엄 내지", feature1Description: "어떤 필기구를 사용해도 뒷면 비침 걱정이 없습니다. 눈의 피로를 덜어주는 미색 용지를 사용합니다.", feature1Stat1Value: "120gsm", feature1Stat1Label: "도톰한 두께감", feature1Stat2Value: "Acid-Free", feature1Stat2Label: "중성지 사용", feature2Badge: "SMART DESIGN", feature2Title: "어떤 페이지도 평평하게\n180도 펼침 제본", feature2Description: "글씨를 쓸 때 손에 걸리는 불편함이 없습니다.\n특수 제본 기술을 적용하여\n첫 장부터 마지막 장까지 완벽하게 펼쳐집니다.", feature2Card1: "180° Lay-flat", feature2Card2: "견고한 하드커버", feature3Title: "당신의 일상을\n디자인하세요", feature3Description: "업무 미팅, 학습 노트, 다이어리 꾸미기까지.\n어떤 용도로 사용해도 만족스러운 경험을 드립니다.\n심플한 디자인으로 데스크테리어 소품으로도 훌륭합니다.", feature3Point1Title: "다양한 내지 구성", feature3Point1Desc: "줄글, 모눈, 무지 중 선택 가능", feature3Point2Title: "편리한 디테일", feature3Point2Desc: "가름끈, 수납 포켓, 밴드 클로저 포함" };
    }
  };

  const handleProductSubmit = async () => {
    if (!productName.trim()) {
      alert('상품명을 입력해주세요.');
      return;
    }

    // preUploaded 템플릿: 바로 상품 추가 모달 표시
    if (selectedTemplate === 'preUploaded') {
      if (!uploadedImages['detail_page']) {
        alert('상세페이지 이미지를 먼저 업로드해주세요.');
        return;
      }

      // 간단한 content 설정 후 바로 모달 표시
      setGeneratedContent({
        productName: productName,
      });
      setShowAddProductModal(true);
      return;
    }

    // 기존 템플릿: AI 생성 프로세스
    setScreen('generating');
    setLoadingStep(0);

    // 이미지 로딩 (병렬로 진행)
    const imageLoadingPromise = (async () => {
      try {
        const images = await imageService.getAutoImages(category);
        setUploadedImages(images);
        console.log('✅ 자동 이미지 로딩 완료:', Object.keys(images).length, '개');
      } catch (error) {
        console.error('❌ 자동 이미지 로딩 실패:', error);
      }
    })();

    const steps = [
      { delay: 800, step: 0 },
      { delay: 1500, step: 1 },
      { delay: 2000, step: 2 },
      { delay: 1000, step: 3 },
    ];

    for (const { delay, step } of steps) {
      await new Promise(resolve => setTimeout(resolve, delay));
      setLoadingStep(step);
    }

    // 이미지 로딩 완료 대기
    await imageLoadingPromise;

    try {
      let content;
      if (selectedTemplate === 'daily') content = await generateDailyContent();
      else if (selectedTemplate === 'convenience') content = await generateFoodContent();
      else if (selectedTemplate === 'electronics') content = await generateElectronicsContent();
      else if (selectedTemplate === 'processedFood') content = await generateProcessedFoodContent();
      else if (selectedTemplate === 'hygiene') content = await generateHygieneContent();
      else if (selectedTemplate === 'stationery') content = await generateStationeryContent();
      else throw new Error('지원되지 않는 템플릿');

      setGeneratedContent(content);
      await new Promise(resolve => setTimeout(resolve, 500));
      setScreen('result');
    } catch (error) {
      console.error('Generation failed:', error);
      alert('AI 콘텐츠 생성 중 오류가 발생했습니다.');
      setScreen('product-input');
    }
  };

  const handleReset = () => {
    setScreen('category-selection');
    setSelectedTemplate(null);
    setCategory({ level1: '', level2: '', level3: '', level4: '' });
    setProductName('');
    setProductUrl('');
    setExtractedThumbnail('');
    setSourcingPrice(null);
    setSellingPrice(null);
    setDetectedSource('');
    setGeneratedContent(null);
    setUploadedImages({});
    setEditingField(null);
    setEditingValue('');
    setShowError(false);
  };

  const handleImageUpload = async (imageKey: string) => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.onchange = async (e: any) => {
      const file = e.target.files?.[0];
      if (file) {
        try {
          // FormData로 파일 전송
          const formData = new FormData();
          formData.append('file', file);

          // Supabase에 업로드
          const response = await fetch(`${API_BASE_URL}/api/products/upload-image`, {
            method: 'POST',
            body: formData,
          });

          if (!response.ok) {
            throw new Error('이미지 업로드 실패');
          }

          const data = await response.json();

          if (data.success && data.url) {
            // Supabase URL 저장
            setUploadedImages(prev => ({ ...prev, [imageKey]: data.url }));
          } else {
            throw new Error('이미지 URL을 받지 못했습니다');
          }
        } catch (error) {
          console.error('이미지 업로드 오류:', error);
          alert('이미지 업로드에 실패했습니다. 다시 시도해주세요.');
        }
      }
    };
    input.click();
  };

  const handleImageDrop = async (imageKey: string, file: File) => {
    try {
      // FormData로 파일 전송
      const formData = new FormData();
      formData.append('file', file);

      // Supabase에 업로드
      const response = await fetch(`${API_BASE_URL}/api/products/upload-image`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('이미지 업로드 실패');
      }

      const data = await response.json();

      if (data.success && data.url) {
        // Supabase URL 저장
        setUploadedImages(prev => ({ ...prev, [imageKey]: data.url }));
      } else {
        throw new Error('이미지 URL을 받지 못했습니다');
      }
    } catch (error) {
      console.error('이미지 업로드 오류:', error);
      alert('이미지 업로드에 실패했습니다. 다시 시도해주세요.');
    }
  };

  const handleDetailPageImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploadingDetailPage(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE_URL}/api/products/upload-image`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('상세페이지 이미지 업로드 실패');
      }

      const data = await response.json();

      if (data.success && data.url) {
        setUploadedImages(prev => ({ ...prev, detail_page: data.url }));
      } else {
        throw new Error('이미지 URL을 받지 못했습니다');
      }
    } catch (error) {
      console.error('상세페이지 이미지 업로드 오류:', error);
      alert('상세페이지 이미지 업로드에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setIsUploadingDetailPage(false);
    }
  };

  const handleImageResize = (imageKey: string, size: number) => {
    setImageSizes(prev => ({ ...prev, [imageKey]: size }));
  };

  const handleImageMove = (imageKey: string, position: { x: number; y: number }) => {
    setImagePositions(prev => ({ ...prev, [imageKey]: position }));
  };

  const handleImageRefresh = async (imageKey: string) => {
    const currentImage = uploadedImages[imageKey];
    if (!currentImage) {
      console.warn('현재 이미지가 없습니다');
      return;
    }

    // Extract folder ID from image URL
    // 로컬 형식: /supabase-images/1_흰밥/...
    // Supabase Storage 형식 1: https://.../product-images/cat-1/...
    // Supabase Storage 형식 2: https://.../product-images/detail-pages/1770647709_xxx.png
    let folderId: string | null = null;

    // Try Supabase Storage format (cat-{id})
    const catMatch = currentImage.match(/\/cat-(\d+)\//);
    if (catMatch) {
      folderId = catMatch[1];
    }

    // Try detail-pages format ({id}_name)
    if (!folderId) {
      const detailPagesMatch = currentImage.match(/\/detail-pages\/(\d+)_/);
      if (detailPagesMatch) {
        folderId = detailPagesMatch[1];
      }
    }

    // Fallback to local format ({id}_name)
    if (!folderId) {
      const localMatch = currentImage.match(/\/supabase-images\/(\d+)_/);
      if (localMatch) {
        folderId = localMatch[1];
      }
    }

    if (!folderId) {
      console.warn('폴더 경로를 찾을 수 없습니다:', currentImage);
      // 이미지 새로고침 대신 토스트 메시지만 표시하고 조용히 리턴
      return;
    }

    console.log('이미지 새로고침 - 폴더 ID:', folderId);

    try {
      // Get all images from the same folder
      const images = await imageService.getImagesFromFolder(folderId);
      if (images.length === 0) {
        console.warn('폴더에 이미지가 없습니다');
        return;
      }

      // Filter out current image
      const otherImages = images.filter(img => img !== currentImage);
      if (otherImages.length === 0) {
        console.warn('교체할 다른 이미지가 없습니다');
        return;
      }

      // Randomly select a different image
      const randomIndex = Math.floor(Math.random() * otherImages.length);
      const newImage = otherImages[randomIndex];

      console.log('새 이미지로 교체:', newImage);

      // Update the image
      setUploadedImages(prev => ({ ...prev, [imageKey]: newImage }));
    } catch (error) {
      console.error('이미지 새로고침 실패:', error);
    }
  };

  // 텍스트 선택 (싱글 클릭) - 우측 패널에 표시
  const handleTextClick = (field: string) => {
    setSelectedElement({ type: 'text', field });
  };

  // 텍스트 더블 클릭 - 인라인 편집 모드
  const handleTextEdit = (field: string, value: string) => {
    setEditingField(field);
    setEditingValue(value);
  };

  const handleTextSave = () => {
    if (editingField && generatedContent) {
      setGeneratedContent(prev => ({ ...prev!, [editingField]: editingValue }));
    }
    setEditingField(null);
    setEditingValue('');
  };

  const handleTextCancel = () => {
    setEditingField(null);
    setEditingValue('');
  };

  // 우측 패널에서 텍스트 내용 변경
  const handleTextChange = (field: string, value: string) => {
    if (generatedContent) {
      setGeneratedContent(prev => ({ ...prev!, [field]: value }));
    }
  };

  // 우측 패널에서 스타일 변경
  const handleStyleChange = (field: string, styles: { fontSize?: string; color?: string; fontWeight?: string; textAlign?: string }) => {
    setTextStyles(prev => ({ ...prev, [field]: { ...prev[field], ...styles } }));
  };

  // 이미지 선택
  const handleImageClickForPanel = (imageKey: string) => {
    setSelectedElement({ type: 'image', field: imageKey });
    setEditingImage(imageKey); // 기존 동작 유지
  };

  const handleTextStyleClick = (field: string) => {
    setEditingTextStyle(field);
  };

  const handleTextStyleChange = (field: string, styles: { fontSize?: string; color?: string; fontWeight?: string }) => {
    setTextStyles(prev => ({ ...prev, [field]: styles }));
  };

  const handleTextStyleClose = () => {
    setEditingTextStyle(null);
  };

  const handleAddImageSlot = () => {
    setAdditionalImageSlots(prev => prev + 1);
  };

  const handleRemoveImageSlot = (index: number) => {
    const imageKey = `additional_product_image_${index}`;
    setUploadedImages(prev => {
      const newImages = { ...prev };
      delete newImages[imageKey];
      return newImages;
    });
    setAdditionalImageSlots(prev => prev - 1);
  };

  const handleDownload = async () => {
    if (!templateRef.current || !generatedContent) return;

    setIsSaving(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 100));

      // 임시로 스타일 백업 및 설정 (너비 강제 고정 + 테두리 제거)
      const originalOutline = templateRef.current.style.outline;
      const originalBorder = templateRef.current.style.border;
      const originalWidth = templateRef.current.style.width;

      templateRef.current.style.outline = 'none';
      templateRef.current.style.border = 'none';
      templateRef.current.style.width = '860px';  // 인라인 스타일로 너비 강제 고정

      // 고화질 JPG 생성
      const dataUrl = await htmlToImage.toJpeg(templateRef.current, {
        quality: 1.0,  // 최고 품질
        pixelRatio: 2,  // 2배 해상도 (860px → 1720px)
        backgroundColor: '#ffffff',
        cacheBust: true,
        filter: (node: HTMLElement) => {
          if (node.classList) {
            return !node.classList.contains('opacity-0') &&
                   !node.classList.contains('group-hover:opacity-100') &&
                   !node.classList.contains('border-2') &&
                   !node.classList.contains('outline') &&
                   node.tagName !== 'INPUT' &&
                   node.tagName !== 'BUTTON' &&
                   !node.hasAttribute('data-exclude-from-download');
          }
          return true;
        }
      });

      // 스타일 복원
      templateRef.current.style.outline = originalOutline;
      templateRef.current.style.border = originalBorder;
      templateRef.current.style.width = originalWidth;

      // DataURL을 Blob으로 변환하여 다운로드
      const response = await fetch(dataUrl);
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
      link.href = url;
      link.download = `${generatedContent.productName.replace(/[^a-zA-Z0-9가-힣]/g, '_')}_상세페이지_${timestamp}.jpg`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      alert('상세페이지가 성공적으로 저장되었습니다!');
    } catch (error) {
      console.error('Download failed:', error);
      const errorMessage = error instanceof Error ? error.message : '알 수 없는 오류';
      alert(`다운로드 중 오류가 발생했습니다.\n\n오류 내용: ${errorMessage}\n\n다시 시도해주세요.`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleThumbnailDownload = async () => {
    if (!extractedThumbnail) return;

    try {
      const response = await fetch(extractedThumbnail);
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
      const fileName = productName
        ? `${productName.replace(/[^a-zA-Z0-9가-힣]/g, '_')}_썸네일_${timestamp}.jpg`
        : `썸네일_${timestamp}.jpg`;
      link.href = url;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (error) {
      console.error('썸네일 다운로드 실패:', error);
      alert('썸네일 다운로드에 실패했습니다.');
    }
  };

  const handleAddToMonitoring = async () => {
    if (!productUrl || !productName) {
      alert('모니터링에 추가하려면 상품 URL이 필요합니다.');
      return;
    }

    setIsAddingToMonitoring(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/monitor/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product_url: productUrl,
          product_name: productName,
          source: detectedSource.toLowerCase() || 'other',
          current_price: sourcingPrice,
          original_price: sourcingPrice,
          check_interval: 15,
          notes: `상세페이지 생성기에서 추가 | 판매가: ${sellingPrice?.toLocaleString()}원 (30% 마진)`
        })
      });

      if (!response.ok) {
        throw new Error('모니터링 추가 실패');
      }

      const result = await response.json();
      alert(`✓ "${productName}" 모니터링이 시작되었습니다!\n\n가격 변동 및 재고 상태를 15분마다 자동으로 체크합니다.`);
    } catch (error) {
      console.error('모니터링 추가 실패:', error);
      alert('모니터링 추가에 실패했습니다. 백엔드 서버를 확인해주세요.');
    } finally {
      setIsAddingToMonitoring(false);
    }
  };

  const renderTemplate = () => {
    if (!generatedContent) return null;

    const templateProps = {
      content: generatedContent,
      uploadedImages,
      editingField,
      editingValue,
      onImageUpload: handleImageUpload,
      onImageRefresh: handleImageRefresh,
      onImageDrop: handleImageDrop,
      onTextEdit: handleTextEdit,
      onTextSave: handleTextSave,
      onTextCancel: handleTextCancel,
      onValueChange: setEditingValue,
      onImageClick: handleImageClickForPanel,
      editingImage,
      imageStyleSettings,
      onTextStyleClick: handleTextClick,
      textStyles,
      additionalImageSlots,
      onAddImageSlot: handleAddImageSlot,
      onRemoveImageSlot: handleRemoveImageSlot,
      imageSizes,
      onImageResize: handleImageResize,
      imagePositions,
      onImageMove: handleImageMove,
      imageAlignments,
      onImageAlignment: handleImageAlignment,
      containerWidths,
      onContainerWidthChange: handleContainerWidthChange,
      hiddenSections,
      onSectionDelete: handleSectionDelete,
      onImageDelete: (key: string) => {
        setUploadedImages(prev => {
          const newImages = { ...prev };
          delete newImages[key];
          return newImages;
        });
      },
    };

    if (selectedTemplate === 'daily') return <DailyTemplate {...templateProps} />;
    if (selectedTemplate === 'convenience') return <FoodTemplate {...templateProps} />;
    if (selectedTemplate === 'electronics') return <ElectronicsTemplate {...templateProps} />;
    if (selectedTemplate === 'processedFood') return <ProcessedFoodTemplate {...templateProps} />;
    if (selectedTemplate === 'hygiene') return <HygieneTemplate {...templateProps} />;
    if (selectedTemplate === 'stationery') return <StationeryTemplate {...templateProps} />;
    if (selectedTemplate === 'preUploaded') return <PreUploadedTemplate {...templateProps} />;
    return null;
  };

  const isCategoryComplete = category.level1 && category.level2 && category.level3 && category.level4;

  return (
    <div className="w-full">
      {screen === 'category-selection' && isCategoryLoading ? (
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="flex flex-col items-center gap-4">
            <RefreshCw className="w-8 h-8 text-blue-600 animate-spin" />
            <p className="text-gray-600">카테고리 정보를 불러오는 중...</p>
          </div>
        </div>
      ) : screen === 'category-selection' ? (
        <CategorySelectionScreen
          category={category}
          level1Options={level1Options}
          level2Options={level2Options}
          level3Options={level3Options}
          level4Options={level4Options}
          isCategoryComplete={isCategoryComplete}
          showError={showError}
          onCategoryChange={handleCategoryChange}
          onTemplateSelect={handleTemplateSelect}
        />
      ) : null}

      {screen === 'product-input' && (
        <ProductInputScreen
          productName={productName}
          productUrl={productUrl}
          selectedTemplate={selectedTemplate}
          sourcingPrice={sourcingPrice}
          sellingPrice={sellingPrice}
          detectedSource={detectedSource}
          manualInputRequired={manualInputRequired}
          manualInputMessage={manualInputMessage}
          onProductNameChange={setProductName}
          onProductUrlChange={setProductUrl}
          onSourcingPriceChange={setSourcingPrice}
          onSellingPriceChange={setSellingPrice}
          extractedThumbnail={extractedThumbnail}
          isExtractingUrl={isExtractingUrl}
          onExtractUrlInfo={extractUrlInfo}
          onThumbnailDownload={handleThumbnailDownload}
          onBack={handleReset}
          onGenerate={handleProductSubmit}
          uploadedDetailPageImage={uploadedImages['detail_page']}
          isUploadingDetailPage={isUploadingDetailPage}
          onDetailPageImageUpload={handleDetailPageImageUpload}
          detailPageInputRef={detailPageInputRef}
        />
      )}

      {screen === 'generating' && (
        <GeneratingScreen productName={productName} loadingStep={loadingStep} />
      )}

      {screen === 'result' && generatedContent && (
        <div className="w-full relative" onClick={handleOutsideClick}>
          {/* 상단 컨트롤 바 */}
          <div className="sticky top-0 bg-white border-b border-gray-200 z-30 shadow-sm">
            <div className="flex justify-between items-center px-6 py-4">
              <button onClick={handleReset} className="flex items-center gap-3 text-gray-600 hover:text-gray-800 transition">
                <ArrowLeft className="w-5 h-5" />
                <span className="font-medium">뒤로가기</span>
              </button>
              <h2 className="text-xl font-bold text-gray-800">{generatedContent.productName} 상세페이지</h2>
              <div className="flex items-center gap-3">
                  {productUrl && (
                    <button
                      onClick={handleAddToMonitoring}
                      disabled={isAddingToMonitoring}
                      className="flex items-center gap-2 px-5 py-2 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-xl hover:from-green-600 hover:to-emerald-700 disabled:opacity-50 transition font-medium shadow-lg"
                    >
                      <Plus className="w-4 h-4" />
                      {isAddingToMonitoring ? '추가 중...' : '모니터링 추가'}
                    </button>
                  )}
                  <button
                    onClick={() => setShowAddProductModal(true)}
                    className="flex items-center gap-2 px-5 py-2 bg-gradient-to-r from-purple-500 to-pink-600 text-white rounded-xl hover:from-purple-600 hover:to-pink-700 transition font-medium shadow-lg"
                  >
                    <ShoppingCart className="w-4 h-4" />
                    상품 추가
                  </button>
                  <button onClick={handleDownload} disabled={isSaving} className="flex items-center gap-2 px-5 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 transition font-medium shadow-lg">
                    <Download className="w-4 h-4" />
                    {isSaving ? '저장 중...' : 'JPG 다운로드'}
                  </button>
                </div>
              </div>
            </div>

          {/* 메인 컨텐츠: 템플릿 + 우측 패널 */}
          <div className="flex">
            {/* 템플릿 영역 */}
            <div className="flex-1 flex justify-center p-6 bg-gray-50 min-h-screen">
              <div className="bg-white w-[860px] shadow-2xl rounded-2xl overflow-hidden border">
                <div ref={templateRef} className="w-[860px]">
                  {renderTemplate()}
                </div>
              </div>
            </div>

            {/* 우측 속성 패널 (Figma 스타일) - 스크롤 따라옴 */}
            <PropertiesPanel
              selectedElement={selectedElement}
              content={generatedContent}
              textStyles={textStyles}
              imageSizes={imageSizes}
              imagePositions={imagePositions}
              uploadedImages={uploadedImages}
              onTextChange={handleTextChange}
              onStyleChange={handleStyleChange}
              onImageResize={handleImageResize}
              onImageMove={handleImageMove}
              containerWidths={containerWidths}
              onContainerWidthChange={handleContainerWidthChange}
              onClose={() => setSelectedElement({ type: null, field: null })}
            />
          </div>
        </div>
      )}

      {/* 텍스트 스타일 편집 모달 */}
      {editingTextStyle && (
        <TextStyleEditor
          field={editingTextStyle}
          styles={textStyles[editingTextStyle] || {}}
          onStyleChange={handleTextStyleChange}
          onClose={handleTextStyleClose}
        />
      )}

      {/* 상품 추가 모달 */}
      {showAddProductModal && generatedContent && (
        <AddProductFromDetailPageModal
          productName={productName}
          category={category}
          productUrl={productUrl}
          sourcingPrice={sourcingPrice}
          sellingPrice={sellingPrice}
          detectedSource={detectedSource}
          extractedThumbnail={extractedThumbnail}
          generatedContent={generatedContent}
          selectedTemplate={selectedTemplate}
          uploadedImages={uploadedImages}
          imageSizes={imageSizes}
          imagePositions={imagePositions}
          textStyles={textStyles}
          templateRef={templateRef}
          inputType={inputType}
          onClose={() => setShowAddProductModal(false)}
          onSuccess={() => {
            setShowAddProductModal(false);
            alert('상품이 성공적으로 추가되었습니다!');
          }}
        />
      )}
    </div>
  );
}

function CategorySelectionScreen({ category, level1Options, level2Options, level3Options, level4Options, isCategoryComplete, showError, onCategoryChange, onTemplateSelect }: any) {
  return (
    <div className="w-full text-center relative min-h-screen">
      <div className="relative z-10 mb-16">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl mb-8 shadow-2xl shadow-blue-500/25">
          <ShoppingCart className="w-8 h-8 text-white" />
        </div>
        <h2 className="text-5xl font-bold bg-gradient-to-r from-gray-900 via-blue-800 to-purple-800 bg-clip-text text-transparent mb-6 tracking-tight">어떤 상품의 상세페이지를 만드시겠어요?</h2>
        <p className="text-xl text-gray-600 font-light max-w-2xl mx-auto leading-relaxed">상품 종류를 선택하시면 AI가 맞춤형 상세페이지를 제작해드립니다</p>
        <div className="w-32 h-1 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 mx-auto mt-8 rounded-full shadow-lg"></div>
      </div>

      <div className="max-w-4xl mx-auto bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl p-8 border border-gray-200">
        <div className="flex items-center justify-center gap-2 mb-6">
          <h3 className="text-2xl font-bold text-gray-800">상세 카테고리 선택</h3>
          <span className="px-3 py-1 bg-red-100 text-red-600 text-sm font-semibold rounded-full">필수</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            { label: '대대분류', value: category.level1, options: level1Options, key: 'level1' },
            { label: '대분류', value: category.level2, options: level2Options, key: 'level2' },
            { label: '중분류', value: category.level3, options: level3Options, key: 'level3' },
            { label: '소분류', value: category.level4, options: level4Options, key: 'level4' },
          ].map(({ label, value, options, key }) => (
            <div key={key}>
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                {label}<span className="text-red-500">*</span>
                {key === 'level1' && showError && (
                  <span className="ml-2 px-3 py-1 bg-red-100 text-red-600 text-sm font-semibold rounded-full">⚠️ 모든 카테고리를 선택해주세요</span>
                )}
              </label>
              <select value={value} onChange={(e) => onCategoryChange(key, e.target.value)} className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none transition">
                <option value="">선택</option>
                {options.map((opt: string) => (<option key={opt} value={opt}>{opt}</option>))}
              </select>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-8 relative z-10 max-w-5xl mx-auto mt-12">
          {Object.entries(templates).map(([key, template], index) => {
            const Icon = getTemplateIcon(key as TemplateType);
            const delays = ['animation-delay-600', 'animation-delay-800', 'animation-delay-1000', 'animation-delay-1200', 'animation-delay-1400', 'animation-delay-1600'];

            return (
              <div key={key} className={`animate-fade-in-up ${delays[index]}`}>
                <div className="relative group">
                  {/* Outer Glow Effect */}
                  <div className="absolute -inset-1 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-3xl blur-lg opacity-0 group-hover:opacity-30 transition-all duration-700"></div>

                  <button
                    onClick={() => onTemplateSelect(key as TemplateType)}
                    disabled={!isCategoryComplete}
                    className={`relative flex flex-col items-center justify-center w-64 h-80 bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl shadow-black/10 hover:shadow-3xl hover:shadow-blue-500/20 transition-all duration-700 transform hover:scale-105 hover:-translate-y-2 group overflow-hidden border border-white/20 ${!isCategoryComplete && 'opacity-50 cursor-not-allowed'}`}
                  >
                    {/* Background Overlay */}
                    <div className="absolute inset-0 bg-gradient-to-br from-white/50 to-gray-50/50 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>

                    {/* Card Hover Particles */}
                    <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-1000">
                      {[...Array(8)].map((_, i) => (
                        <div
                          key={i}
                          className="absolute w-1 h-1 bg-gradient-to-r from-blue-400 to-purple-400 rounded-full animate-pulse"
                          style={{
                            left: `${20 + i * 10}%`,
                            top: `${30 + (i % 3) * 20}%`,
                            animationDelay: `${i * 0.2}s`,
                            animationDuration: '2s'
                          }}
                        ></div>
                      ))}
                    </div>

                    {/* Icon Container */}
                    <div className={`relative w-28 h-28 rounded-3xl flex items-center justify-center mb-6 transform transition-all duration-700 group-hover:rotate-3 group-hover:scale-110 shadow-2xl shadow-blue-500/25 ${isCategoryComplete ? 'bg-gradient-to-br from-blue-500 to-purple-600' : 'bg-gray-400'}`}>
                      {/* Ping Border Effect */}
                      <div className="absolute inset-0 rounded-3xl border-2 border-white/30 opacity-0 group-hover:opacity-100 animate-ping"></div>
                      {/* Pulse Inner Border */}
                      <div className="absolute inset-2 rounded-2xl border border-white/20 opacity-0 group-hover:opacity-50 animate-pulse"></div>
                      {/* Icon */}
                      <div className="transform transition-transform duration-500 group-hover:scale-110 text-white">
                        <Icon className="w-10 h-10 text-white" />
                      </div>
                    </div>

                    {/* Text */}
                    <div className="text-center transform transition-all duration-500 group-hover:translate-y-1 relative z-10">
                      <h3 className="text-2xl font-bold text-gray-800 mb-2 group-hover:text-blue-600 transition-colors duration-500">{template.name}</h3>
                      <p className="text-gray-500 group-hover:text-gray-700 transition-colors duration-500 px-4 font-light">{template.description}</p>
                    </div>

                    {/* Success Checkmark */}
                    {isCategoryComplete && (
                      <div className="absolute top-4 right-4 w-8 h-8 bg-gradient-to-br from-green-400 to-green-600 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transform scale-0 group-hover:scale-100 transition-all duration-500 shadow-lg">
                        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                    )}

                    {/* Bottom Progress Bar */}
                    <div className="absolute bottom-0 left-0 h-1 bg-gradient-to-r from-blue-500 to-purple-600 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-1000 origin-left w-full rounded-b-3xl"></div>
                  </button>
                </div>
              </div>
            );
          })}
      </div>
    </div>
  );
}

function ProductInputScreen({
  productName,
  productUrl,
  selectedTemplate,
  sourcingPrice,
  sellingPrice,
  detectedSource,
  manualInputRequired,
  manualInputMessage,
  onProductNameChange,
  onProductUrlChange,
  onSourcingPriceChange,
  onSellingPriceChange,
  extractedThumbnail,
  isExtractingUrl,
  onExtractUrlInfo,
  onThumbnailDownload,
  onBack,
  onGenerate,
  uploadedDetailPageImage,
  isUploadingDetailPage,
  onDetailPageImageUpload,
  detailPageInputRef
}: any) {
  const template = selectedTemplate ? (templates as any)[selectedTemplate] : null;
  const Icon = selectedTemplate ? getTemplateIcon(selectedTemplate) : Sparkles;
  const isPreUploaded = selectedTemplate === 'preUploaded';

  return (
    <div className="max-w-2xl mx-auto text-center relative min-h-screen py-8">
      <div className="relative z-10">
        <button onClick={onBack} className="mb-6 flex items-center gap-2 text-gray-600 hover:text-gray-800 transition"><ArrowLeft className="w-5 h-5" />뒤로가기</button>
        <div className="mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl mb-4 shadow-2xl shadow-blue-500/25 animate-pulse">
            <Icon className="w-10 h-10 text-white" />
          </div>
          <h2 className="text-4xl font-bold text-gray-800 mb-2">상품 정보 입력</h2>
          <p className="text-gray-600">선택한 템플릿: {template?.name}</p>
        </div>
        <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl p-8 border border-white/20 space-y-6">
          {/* URL 입력 섹션 */}
          <div>
            <label className="block text-left text-sm font-semibold text-gray-700 mb-2">
              상품 URL (선택사항)
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={productUrl}
                onChange={(e) => onProductUrlChange(e.target.value)}
                placeholder="SSG, 11번가, G마켓, 오뚜기몰 등 상품 URL 입력..."
                className="flex-1 px-6 py-4 border-2 border-gray-200 rounded-xl focus:border-purple-500 focus:outline-none transition-all duration-300 text-lg focus:shadow-lg focus:shadow-purple-500/20"
              />
              <button
                onClick={onExtractUrlInfo}
                disabled={isExtractingUrl || !productUrl}
                className="bg-purple-600 text-white px-6 py-4 rounded-xl font-semibold hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 whitespace-nowrap"
              >
                {isExtractingUrl ? (
                  <>
                    <RefreshCw className="w-5 h-5 animate-spin" />
                    확인중...
                  </>
                ) : (
                  <>
                    <Search className="w-5 h-5" />
                    URL 확인
                  </>
                )}
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-2 text-left">
              URL을 입력하면 상품명, 가격, 썸네일을 자동으로 가져옵니다
            </p>
            {detectedSource && (
              <div className="mt-2 flex items-center gap-2">
                <span className="text-sm font-semibold text-blue-600">✓ 감지된 마켓: {detectedSource}</span>
              </div>
            )}
            {manualInputRequired && manualInputMessage && (
              <div className="mt-4 bg-yellow-50 border-2 border-yellow-300 rounded-xl p-4">
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                  <div className="text-left">
                    <h4 className="font-semibold text-yellow-900 mb-1">수동 입력 필요</h4>
                    <p className="text-sm text-yellow-800">{manualInputMessage}</p>
                    <p className="text-xs text-yellow-700 mt-2">상품명과 썸네일은 자동으로 추출되었습니다. 아래 가격 정보를 직접 입력해주세요.</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* 가격 정보 표시 (항상 표시) */}
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-6 border-2 border-blue-200">
            <h3 className="text-sm font-bold text-gray-700 mb-4 flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-blue-600" />
              가격 정보 {manualInputRequired ? '(직접 입력)' : '(30% 마진 자동 계산)'}
            </h3>
            {manualInputRequired ? (
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-white rounded-lg p-4 border border-gray-200">
                  <label className="block text-xs text-gray-500 mb-2">소싱가 (원가) *</label>
                  <input
                    type="number"
                    value={sourcingPrice || ''}
                    onChange={(e) => {
                      const price = parseFloat(e.target.value);
                      onSourcingPriceChange(price);
                      if (price > 0) {
                        onSellingPriceChange(Math.ceil(price * 1.3));
                      }
                    }}
                    placeholder="소싱가 입력"
                    className="w-full text-xl font-bold text-gray-800 border-b-2 border-gray-300 focus:border-blue-500 outline-none py-1"
                  />
                </div>
                <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg p-4 shadow-lg">
                  <label className="block text-xs text-white/80 mb-2">판매가 (30% 마진) *</label>
                  <input
                    type="number"
                    value={sellingPrice || ''}
                    onChange={(e) => onSellingPriceChange(parseFloat(e.target.value))}
                    placeholder="판매가 입력"
                    className="w-full text-xl font-bold text-white bg-transparent border-b-2 border-white/50 focus:border-white outline-none py-1 placeholder-white/50"
                  />
                </div>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-white rounded-lg p-4 border border-gray-200">
                    <p className="text-xs text-gray-500 mb-1">소싱가 (원가)</p>
                    <p className="text-2xl font-bold text-gray-800">
                      {sourcingPrice ? `${sourcingPrice.toLocaleString()}원` : '추출 대기 중...'}
                    </p>
                  </div>
                  <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg p-4 shadow-lg">
                    <p className="text-xs text-white/80 mb-1">판매가 (30% 마진)</p>
                    <p className="text-2xl font-bold text-white">
                      {sellingPrice ? `${sellingPrice.toLocaleString()}원` : '추출 대기 중...'}
                    </p>
                  </div>
                </div>
                <div className="mt-3 bg-white rounded-lg p-3 border border-gray-200">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">순이익 (30% 마진)</span>
                    <span className="font-bold text-green-600">
                      {sourcingPrice ? `+${Math.ceil(sourcingPrice * 0.3).toLocaleString()}원` : '-'}
                    </span>
                  </div>
                </div>
              </>
            )}
          </div>

          {/* 썸네일 미리보기 (항상 표시) */}
          <div className="bg-gray-50 rounded-xl p-4 border-2 border-gray-200">
            <p className="text-sm font-semibold text-gray-700 mb-3 text-left">추출된 썸네일</p>
            {extractedThumbnail ? (
              <div className="relative w-full max-w-xs mx-auto">
                <img
                  src={extractedThumbnail}
                  alt="상품 썸네일"
                  className="w-full rounded-lg shadow-lg"
                  onError={(e) => {
                    e.currentTarget.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="200"%3E%3Crect fill="%23ddd" width="200" height="200"/%3E%3Ctext fill="%23999" font-size="16" x="50%25" y="50%25" text-anchor="middle" dominant-baseline="middle"%3E이미지 로드 실패%3C/text%3E%3C/svg%3E';
                  }}
                />
                <a
                  href={productUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="absolute top-2 right-2 bg-white/90 backdrop-blur-sm p-2 rounded-lg hover:bg-white transition-colors shadow-lg"
                >
                  <ExternalLink className="w-4 h-4 text-gray-600" />
                </a>
              </div>
            ) : (
              <div className="w-full max-w-xs mx-auto h-48 bg-gray-100 rounded-lg border-2 border-dashed border-gray-300 flex items-center justify-center">
                <p className="text-gray-400 text-sm">URL 확인 후 자동 추출됩니다</p>
              </div>
            )}
            {extractedThumbnail && (
              <button
                onClick={onThumbnailDownload}
                className="mt-3 w-full flex items-center justify-center gap-2 px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-lg hover:from-green-600 hover:to-emerald-700 transition-all duration-300 font-medium shadow-md"
              >
                <Download className="w-4 h-4" />
                썸네일 저장
              </button>
            )}
          </div>

          {/* 상세페이지 업로드 섹션 (preUploaded 템플릿만) */}
          {isPreUploaded && (
            <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-xl p-6 border-2 border-green-200">
              <h3 className="text-sm font-bold text-gray-700 mb-4 flex items-center gap-2">
                <Upload className="w-4 h-4 text-green-600" />
                상세페이지 이미지 업로드
              </h3>
              <input
                ref={detailPageInputRef}
                type="file"
                accept="image/*"
                onChange={onDetailPageImageUpload}
                className="hidden"
              />
              {uploadedDetailPageImage ? (
                <div className="space-y-3">
                  <div className="relative w-full max-w-xs mx-auto">
                    <img
                      src={uploadedDetailPageImage}
                      alt="상세페이지"
                      className="w-full rounded-lg shadow-lg border-2 border-green-300"
                    />
                  </div>
                  <button
                    onClick={() => detailPageInputRef.current?.click()}
                    className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all duration-300 font-medium shadow-md"
                  >
                    <Upload className="w-4 h-4" />
                    다른 이미지로 변경
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => detailPageInputRef.current?.click()}
                  disabled={isUploadingDetailPage}
                  className="w-full h-48 bg-white border-2 border-dashed border-green-300 rounded-lg hover:border-green-500 hover:bg-green-50 transition-all duration-300 flex flex-col items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isUploadingDetailPage ? (
                    <>
                      <RefreshCw className="w-8 h-8 text-green-600 animate-spin" />
                      <p className="text-green-600 font-medium">업로드 중...</p>
                    </>
                  ) : (
                    <>
                      <Upload className="w-12 h-12 text-green-600" />
                      <div className="text-center">
                        <p className="text-green-600 font-semibold mb-1">상세페이지 이미지 업로드</p>
                        <p className="text-gray-500 text-sm">클릭하여 이미지 선택</p>
                      </div>
                    </>
                  )}
                </button>
              )}
            </div>
          )}

          {/* 상품명 입력 */}
          <div>
            <label className="block text-left text-sm font-semibold text-gray-700 mb-2">상품명</label>
            <input
              type="text"
              value={productName}
              onChange={(e) => onProductNameChange(e.target.value)}
              placeholder="예: CJ 비비고 소고기 미역국 500g"
              className="w-full px-6 py-4 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none transition-all duration-300 text-lg focus:shadow-lg focus:shadow-blue-500/20"
            />
          </div>

          {/* 버튼: preUploaded는 "상품 추가하기", 나머지는 "AI 상세페이지 생성하기" */}
          <button
            onClick={onGenerate}
            disabled={isPreUploaded ? (!productName.trim() || !uploadedDetailPageImage) : !productName.trim()}
            className="w-full px-8 py-4 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 font-semibold text-lg shadow-lg hover:shadow-xl hover:shadow-blue-500/30 transform hover:scale-105 flex items-center justify-center gap-3 group"
          >
            {isPreUploaded ? (
              <>
                <ShoppingCart className="w-6 h-6 group-hover:scale-110 transition-transform duration-300" />
                상품 추가하기
              </>
            ) : (
              <>
                <Sparkles className="w-6 h-6 group-hover:rotate-12 transition-transform duration-300" />
                AI 상세페이지 생성하기
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

function GeneratingScreen({ productName, loadingStep }: any) {
  const steps = [
    { title: '키워드 분석 중', description: `"${productName}" 상품을 분석하고 있습니다`, icon: '🔍' },
    { title: 'AI 콘텐츠 생성 중', description: '마케팅 전문가 AI가 매력적인 문구를 작성하고 있습니다', icon: '✨' },
    { title: '템플릿 적용 중', description: '전문적인 디자인 템플릿을 적용하고 있습니다', icon: '🎨' },
    { title: '최종 검토 중', description: '상세페이지를 완성하고 있습니다', icon: '✅' },
  ];

  return (
    <div className="max-w-2xl mx-auto text-center relative min-h-screen py-8">
      <div className="relative z-10">
        <div className="mb-12">
          <h2 className="text-5xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-4 animate-pulse">AI 생성 중...</h2>
          <p className="text-gray-600 text-lg">잠시만 기다려주세요</p>
        </div>

        <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl p-12 border border-white/20">
          <div className="space-y-8">
            {steps.map((step, index) => (
              <div key={index} className="relative">
                {/* Active Step Glow Effect */}
                {index === loadingStep && (
                  <div className="absolute -inset-2 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-3xl blur-lg opacity-30 animate-pulse"></div>
                )}

                <div className={`relative flex items-start gap-4 p-6 rounded-2xl transition-all duration-500 ${index <= loadingStep ? 'bg-gradient-to-r from-blue-50 to-purple-50 border-2 border-blue-200 shadow-lg shadow-blue-500/20' : 'bg-gray-50 border-2 border-gray-200'}`}>
                  {/* Step Icon with Animation */}
                  <div className={`text-4xl transform transition-all duration-500 ${index === loadingStep ? 'scale-110 animate-bounce' : 'scale-100'}`}>
                    {step.icon}
                  </div>

                  <div className="flex-1 text-left">
                    <h3 className={`text-xl font-bold mb-1 transition-colors duration-500 ${index <= loadingStep ? 'text-blue-600' : 'text-gray-400'}`}>
                      {step.title}
                    </h3>
                    <p className={`text-sm transition-colors duration-500 ${index <= loadingStep ? 'text-gray-700' : 'text-gray-400'}`}>
                      {step.description}
                    </p>

                    {/* Enhanced Progress Bar */}
                    {index === loadingStep && (
                      <div className="mt-3 relative">
                        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-full animate-pulse shadow-lg shadow-blue-500/50 transition-all duration-1000" style={{ width: '70%' }}></div>
                        </div>
                        {/* Progress Bar Particles */}
                        <div className="absolute inset-0 flex items-center justify-around pointer-events-none">
                          {[...Array(5)].map((_, i) => (
                            <div key={i} className="w-1 h-1 bg-blue-400 rounded-full animate-ping" style={{ animationDelay: `${i * 0.3}s`, animationDuration: '1.5s' }}></div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Status Indicator with Enhanced Animation */}
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center transition-all duration-500 ${index <= loadingStep ? 'bg-gradient-to-br from-blue-500 to-purple-600 shadow-lg shadow-blue-500/50' : 'bg-gray-300'} ${index === loadingStep ? 'animate-pulse scale-110' : 'scale-100'}`}>
                    {index < loadingStep && <CheckCircle className="w-4 h-4 text-white animate-bounce" />}
                    {index === loadingStep && (
                      <div className="w-2 h-2 bg-white rounded-full animate-ping"></div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// 이미지를 최소 600x600으로 리사이즈하는 함수
async function resizeImageToMinimum(file: File, minSize: number = 600): Promise<Blob> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      let { width, height } = img;

      // 이미지가 이미 최소 크기 이상이면 원본 반환
      if (width >= minSize && height >= minSize) {
        resolve(file);
        return;
      }

      // 비율을 유지하면서 최소 크기로 확대
      const scale = Math.max(minSize / width, minSize / height);
      const newWidth = Math.ceil(width * scale);
      const newHeight = Math.ceil(height * scale);

      const canvas = document.createElement('canvas');
      canvas.width = newWidth;
      canvas.height = newHeight;

      const ctx = canvas.getContext('2d');
      if (!ctx) {
        reject(new Error('Canvas context not available'));
        return;
      }

      // 고품질 리사이즈 설정
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = 'high';
      ctx.drawImage(img, 0, 0, newWidth, newHeight);

      canvas.toBlob(
        (blob) => {
          if (blob) {
            resolve(blob);
          } else {
            reject(new Error('Failed to create blob'));
          }
        },
        'image/jpeg',
        0.95
      );
    };
    img.onerror = () => reject(new Error('Failed to load image'));
    img.src = URL.createObjectURL(file);
  });
}

// 상품 추가 모달 (상세페이지 생성기에서)
function AddProductFromDetailPageModal({
  productName,
  category,
  productUrl,
  sourcingPrice,
  sellingPrice,
  detectedSource,
  extractedThumbnail,
  generatedContent,
  selectedTemplate,
  uploadedImages,
  imageSizes,
  imagePositions,
  textStyles,
  templateRef,
  inputType,
  onClose,
  onSuccess
}: {
  productName: string;
  category: Category;
  productUrl: string;
  sourcingPrice: number | null;
  sellingPrice: number | null;
  detectedSource: string;
  extractedThumbnail: string;
  generatedContent: GeneratedContent;
  selectedTemplate: TemplateType | null;
  uploadedImages: Record<string, string>;
  imageSizes: Record<string, number>;
  imagePositions: Record<string, { x: number; y: number }>;
  textStyles: Record<string, { fontSize?: string; color?: string; fontWeight?: string; textAlign?: string }>;
  templateRef?: React.RefObject<HTMLDivElement | null>;
  inputType: 'auto' | 'manual';
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [formData, setFormData] = useState({
    product_name: productName,
    selling_price: sellingPrice?.toString() || '',
    sourcing_url: productUrl,
    sourcing_price: sourcingPrice?.toString() || '',
    sourcing_source: detectedSource.toLowerCase() || '',
    thumbnail_url: extractedThumbnail,
    weight: '',  // 상품 중량 (쿠팡 옵션용)
    ship_price_type: '선결제' as '선결제' | '무료',  // 배송비 타입
    ship_price: '3000',  // 배송비 (선결제인 경우)
    notes: '',
  });
  const [keywords, setKeywords] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [thumbnailPreview, setThumbnailPreview] = useState(extractedThumbnail);
  const [isUploadingThumbnail, setIsUploadingThumbnail] = useState(false);
  const [isGeneratingKeywords, setIsGeneratingKeywords] = useState(false);
  const thumbnailInputRef = useRef<HTMLInputElement>(null);

  // 마켓별 옵션 상태
  // 조합형 옵션 (쿠팡, 지마켓/옥션): {옵션명: [옵션값들]} 형태
  const [gmkOpts, setGmkOpts] = useState<Record<string, string[]>>({});  // 지마켓/옥션 (조합형)
  const [coupangOpts, setCoupangOpts] = useState<Record<string, string[]>>({
    '수량': ['1개'],
    '개당 중량': [formData.weight || '500g']
  });  // 쿠팡 (조합형)

  // 독립형 옵션 (스마트스토어): [{opt_name, opt_value, stock_cnt}] 형태 (기존 방식)
  const [smartOpts, setSmartOpts] = useState<any[]>([
    { opt_name: '상품선택', opt_value: productName || '', stock_cnt: 999 }
  ]);  // 스마트스토어 (독립형)

  // 컴포넌트 마운트 시 자동으로 키워드 생성 (Next.js API Route 사용)
  useEffect(() => {
    const generateKeywordsOnMount = async () => {
      if (!productName) return;

      setIsGeneratingKeywords(true);
      try {
        const categoryString = category.level1 && category.level2 && category.level3 && category.level4
          ? `${category.level1} > ${category.level2} > ${category.level3} > ${category.level4}`
          : undefined;

        const response = await fetch('/api/generate-keywords', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            product_name: productName,
            category: categoryString,
            count: 30
          })
        });

        const data = await response.json();

        if (data.success && data.keywords) {
          setKeywords(data.keywords.slice(0, 40));
        }
      } catch (error) {
        console.error('키워드 자동 생성 실패:', error);
      } finally {
        setIsGeneratingKeywords(false);
      }
    };

    generateKeywordsOnMount();
  }, [productName, category]);

  // 썸네일 이미지 업로드 핸들러
  const handleThumbnailUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploadingThumbnail(true);
    try {
      // 이미지를 최소 600x600으로 리사이즈
      const resizedBlob = await resizeImageToMinimum(file, 600);

      // FormData로 전송
      const uploadFormData = new FormData();
      uploadFormData.append('file', resizedBlob, file.name);

      const response = await fetch(`${API_BASE_URL}/api/products/upload-image`, {
        method: 'POST',
        body: uploadFormData,
      });

      if (!response.ok) {
        throw new Error('썸네일 업로드 실패');
      }

      const data = await response.json();
      if (data.success && data.url) {
        setThumbnailPreview(data.url);
        setFormData(prev => ({ ...prev, thumbnail_url: data.url }));
      }
    } catch (error) {
      console.error('썸네일 업로드 오류:', error);
      alert('썸네일 업로드에 실패했습니다.');
    } finally {
      setIsUploadingThumbnail(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.product_name || !formData.selling_price) {
      alert('상품명과 판매가는 필수입니다.');
      return;
    }

    if (!category.level1 || !category.level2 || !category.level3 || !category.level4) {
      alert('카테고리를 모두 선택해주세요.');
      return;
    }

    setLoading(true);
    try {
      const categoryString = `${category.level1} > ${category.level2} > ${category.level3} > ${category.level4}`;

      // 1. 템플릿을 JPG로 렌더링 (position: absolute 등 모든 CSS 보존)
      let detailImageUrl = '';

      // preUploaded 템플릿: 이미 업로드된 이미지 사용
      if (selectedTemplate === 'preUploaded' && uploadedImages['detail_page']) {
        detailImageUrl = uploadedImages['detail_page'];
        console.log('✅ preUploaded 템플릿: 업로드된 상세페이지 이미지 사용:', detailImageUrl);
      }
      // 기존 템플릿: templateRef로 캡처
      else if (templateRef?.current) {
        try {
          // 임시로 스타일 백업 및 설정 (너비 강제 고정 + 테두리 제거)
          const originalOutline = templateRef.current.style.outline;
          const originalBorder = templateRef.current.style.border;
          const originalWidth = templateRef.current.style.width;

          templateRef.current.style.outline = 'none';
          templateRef.current.style.border = 'none';
          templateRef.current.style.width = '860px';  // 인라인 스타일로 너비 강제 고정

          // 고화질 JPG 생성
          const dataUrl = await htmlToImage.toJpeg(templateRef.current, {
            quality: 1.0,  // 최고 품질
            pixelRatio: 2,  // 2배 해상도 (860px → 1720px)
            backgroundColor: '#ffffff',
            cacheBust: true,
            filter: (node: HTMLElement) => {
              if (node.classList) {
                // 편집 UI 요소 제외
                return !node.classList.contains('opacity-0') &&
                       !node.classList.contains('group-hover:opacity-100') &&
                       !node.classList.contains('border-2') &&
                       !node.classList.contains('outline') &&
                       node.tagName !== 'INPUT' &&
                       node.tagName !== 'BUTTON' &&
                       !node.hasAttribute('data-exclude-from-download');
              }
              return true;
            }
          });

          // 스타일 복원
          templateRef.current.style.outline = originalOutline;
          templateRef.current.style.border = originalBorder;
          templateRef.current.style.width = originalWidth;

          // DataURL을 Blob으로 변환
          const response = await fetch(dataUrl);
          const blob = await response.blob();

          // Supabase에 업로드
          const formData = new FormData();
          formData.append('file', blob, `${productName.replace(/[^a-zA-Z0-9가-힣]/g, '_')}_detail.jpg`);

          const uploadResponse = await fetch(`${API_BASE_URL}/api/products/upload-image`, {
            method: 'POST',
            body: formData,
          });

          if (uploadResponse.ok) {
            const uploadData = await uploadResponse.json();
            if (uploadData.success && uploadData.url) {
              detailImageUrl = uploadData.url;
              console.log('✅ 상세페이지 JPG 업로드 성공:', detailImageUrl);
            }
          }
        } catch (error) {
          console.error('❌ 상세페이지 JPG 생성 실패:', error);
          // 실패해도 계속 진행 (JSON 방식 폴백)
        }
      }

      // 2. 상세페이지 데이터를 JSON으로 저장 (편집용)
      const detailPageData = JSON.stringify({
        template: selectedTemplate,
        content: generatedContent,
        images: uploadedImages,
        imageSizes: imageSizes,
        imagePositions: imagePositions,
        textStyles: textStyles,
        detailImageUrl: detailImageUrl, // JPG URL 저장
        createdAt: new Date().toISOString()
      });

      // 썸네일 URL 결정 (이미 업로드된 경우 그대로 사용)
      let thumbnailUrl = thumbnailPreview || formData.thumbnail_url;

      // 외부 URL인 경우에만 서버에 저장 (이미 supabase URL이면 스킵)
      if (thumbnailUrl && thumbnailUrl.startsWith('http') && !thumbnailUrl.includes('supabase')) {
        try {
          const response = await fetch(`${API_BASE_URL}/api/monitor/save-thumbnail`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              image_url: thumbnailUrl,
              product_name: formData.product_name
            })
          });

          if (response.ok) {
            const result = await response.json();
            if (result.success && result.thumbnail_path) {
              thumbnailUrl = result.thumbnail_path;
            }
          }
        } catch (error) {
          console.error('썸네일 저장 실패:', error);
        }
      }

      // 옵션은 원본 형태로 DB에 저장 (PlayAuto API 호출 시에만 변환)

      // 상품 등록 API 호출
      const response = await fetch(`${API_BASE_URL}/api/products/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product_name: formData.product_name,
          selling_price: parseFloat(formData.selling_price),
          sourcing_url: formData.sourcing_url || undefined,
          sourcing_product_name: formData.product_name,
          sourcing_price: formData.sourcing_price ? parseFloat(formData.sourcing_price) : undefined,
          sourcing_source: formData.sourcing_source || undefined,
          thumbnail_url: thumbnailUrl || undefined,
          original_thumbnail_url: thumbnailPreview || extractedThumbnail || undefined,  // 원본 외부 URL 저장
          category: categoryString,
          detail_page_data: detailPageData,
          weight: formData.weight || undefined,  // 상품 중량 (쿠팡 옵션용)
          ship_price_type: formData.ship_price_type,  // 배송비 타입
          ship_price: formData.ship_price_type === '선결제' ? parseInt(formData.ship_price) : undefined,  // 배송비
          notes: formData.notes || undefined,
          keywords: keywords.length > 0 ? keywords : undefined,  // 키워드 전송
          input_type: inputType,  // 입력 방식: auto(자동추출), manual(수동입력)
          // 마켓별 옵션 저장 (원본 형태 그대로 저장)
          // 조합형(객체): {"색상": ["빨강", "파랑"]}, 독립형(배열): [{opt_name, opt_value}]
          gmk_opts: Object.keys(gmkOpts).length > 0 ? JSON.stringify(gmkOpts) : undefined,
          coupang_opts: Object.keys(coupangOpts).length > 0 ? JSON.stringify(coupangOpts) : undefined,
          smart_opts: smartOpts.length > 0 ? JSON.stringify(smartOpts) : undefined,
        }),
      });

      const data = await response.json();

      if (data.success) {
        onSuccess();
      } else {
        alert('상품 등록에 실패했습니다.');
      }
    } catch (error) {
      console.error('상품 등록 실패:', error);
      alert('상품 등록 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
        <div className="sticky top-0 bg-white border-b border-gray-200 p-6 flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-800">상품 추가</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* 카테고리 정보 표시 */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="text-sm font-semibold text-blue-800 mb-2">선택된 카테고리</div>
            <div className="text-sm text-blue-700">
              {category.level1} &gt; {category.level2} &gt; {category.level3} &gt; {category.level4}
            </div>
          </div>

          {/* 썸네일 미리보기 및 편집 */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="text-sm font-semibold text-gray-700">썸네일</div>
              <button
                type="button"
                onClick={() => thumbnailInputRef.current?.click()}
                disabled={isUploadingThumbnail}
                className="text-sm text-blue-600 hover:text-blue-800 font-medium disabled:opacity-50"
              >
                {isUploadingThumbnail ? '업로드 중...' : '이미지 변경'}
              </button>
            </div>
            <input
              ref={thumbnailInputRef}
              type="file"
              accept="image/*"
              onChange={handleThumbnailUpload}
              className="hidden"
            />
            {thumbnailPreview ? (
              <div className="relative inline-block">
                <img
                  src={thumbnailPreview}
                  alt="상품 썸네일"
                  className="w-32 h-32 object-cover rounded-lg border border-gray-300"
                />
                {isUploadingThumbnail && (
                  <div className="absolute inset-0 bg-black/50 rounded-lg flex items-center justify-center">
                    <RefreshCw className="w-6 h-6 text-white animate-spin" />
                  </div>
                )}
              </div>
            ) : (
              <button
                type="button"
                onClick={() => thumbnailInputRef.current?.click()}
                disabled={isUploadingThumbnail}
                className="w-32 h-32 border-2 border-dashed border-gray-300 rounded-lg flex flex-col items-center justify-center text-gray-400 hover:border-blue-400 hover:text-blue-500 transition-colors"
              >
                <Plus className="w-6 h-6 mb-1" />
                <span className="text-xs">썸네일 추가</span>
              </button>
            )}
            <p className="text-xs text-gray-500 mt-2">
              600x600 미만 이미지는 자동으로 확대됩니다
            </p>
          </div>

          {/* 상품명 */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              상품명 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.product_name}
              onChange={(e) => setFormData({ ...formData, product_name: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="예: 비비고 만두"
              required
            />
          </div>

          {/* 판매가 */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              판매가 <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              value={formData.selling_price}
              onChange={(e) => setFormData({ ...formData, selling_price: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="예: 5000"
              required
            />
            {formData.sourcing_price && (
              <p className="text-xs text-gray-500 mt-1">
                마진: {(parseFloat(formData.selling_price || '0') - parseFloat(formData.sourcing_price)).toLocaleString()}원
                ({((parseFloat(formData.selling_price || '0') - parseFloat(formData.sourcing_price)) / parseFloat(formData.sourcing_price) * 100).toFixed(1)}%)
              </p>
            )}
          </div>

          {/* 마켓별 옵션 설정 */}
          <div className="bg-gradient-to-r from-orange-50 to-yellow-50 border-2 border-orange-300 rounded-xl p-5">
            <div className="flex items-center gap-2 mb-4">
              <ShoppingCart className="w-5 h-5 text-orange-600" />
              <h3 className="text-lg font-bold text-orange-800">마켓별 옵션 설정</h3>
            </div>
            <p className="text-xs text-orange-600 mb-4 bg-white/70 rounded-lg p-2 border border-orange-200">
              💡 상품 등록 시 각 마켓에 전송되는 옵션값입니다. 최대 3개까지 추가 가능합니다.
            </p>

            {/* 지마켓/옥션 옵션 (조합형) */}
            <div className="bg-white border border-blue-200 rounded-lg p-4 mb-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-semibold text-blue-800">🏪 지마켓/옥션 옵션 {Object.keys(gmkOpts).length === 0 ? '(옵션없음)' : '(조합형)'}</h4>
                {Object.keys(gmkOpts).length < 3 && (
                  <button
                    type="button"
                    onClick={() => {
                      const newKey = `옵션${Object.keys(gmkOpts).length + 1}`;
                      setGmkOpts({...gmkOpts, [newKey]: ['']});
                    }}
                    className="flex items-center gap-1 px-3 py-1 bg-blue-500 text-white text-xs rounded-lg hover:bg-blue-600 transition"
                  >
                    <Plus className="w-3 h-3" />
                    옵션 추가
                  </button>
                )}
              </div>
              <p className="text-xs text-blue-600 mb-3">💡 옵션값을 쉼표(,)로 구분하여 입력하면 모든 조합이 자동 생성됩니다 (예: 빨강,파랑,노랑)</p>
              {Object.keys(gmkOpts).length === 0 ? (
                <p className="text-xs text-gray-500 text-center py-2">옵션이 없으면 단일상품으로 등록됩니다</p>
              ) : (
                <div className="space-y-3">
                  {Object.entries(gmkOpts).map(([optName, optValues], index) => (
                    <div key={index} className="border border-blue-100 rounded-lg p-3 relative">
                      <button
                        type="button"
                        onClick={() => {
                          const newOpts = {...gmkOpts};
                          delete newOpts[optName];
                          setGmkOpts(newOpts);
                        }}
                        className="absolute top-2 right-2 text-red-500 hover:text-red-700"
                      >
                        <Tag className="w-4 h-4" />
                      </button>
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="text-xs text-gray-600">옵션명</label>
                          <input
                            type="text"
                            value={optName}
                            onChange={(e) => {
                              const newOpts = {...gmkOpts};
                              delete newOpts[optName];
                              newOpts[e.target.value] = optValues;
                              setGmkOpts(newOpts);
                            }}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') e.preventDefault();
                            }}
                            className="w-full px-2 py-1 text-sm border border-blue-300 rounded focus:ring-1 focus:ring-blue-500"
                            placeholder="예: 색상"
                          />
                        </div>
                        <div>
                          <label className="text-xs text-gray-600">옵션값 (쉼표로 구분)</label>
                          <input
                            type="text"
                            value={optValues.join(',')}
                            onChange={(e) => {
                              const values = e.target.value.split(',').map(v => v.trim());
                              setGmkOpts({...gmkOpts, [optName]: values});
                            }}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') e.preventDefault();
                            }}
                            className="w-full px-2 py-1 text-sm border border-blue-300 rounded focus:ring-1 focus:ring-blue-500"
                            placeholder="예: 빨강,파랑,노랑"
                          />
                        </div>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        생성될 옵션: {optValues.filter(v => v).join(', ')} ({optValues.filter(v => v).length}개)
                      </p>
                    </div>
                  ))}
                  {Object.keys(gmkOpts).length > 1 && (
                    <div className="bg-blue-50 border border-blue-200 rounded p-2">
                      <p className="text-xs text-blue-800">
                        📦 총 {Object.values(gmkOpts).reduce((acc, vals) => acc * vals.filter(v => v).length, 1)}개 조합이 생성됩니다
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* 쿠팡 옵션 (조합형) */}
            <div className="bg-white border border-orange-200 rounded-lg p-4 mb-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-semibold text-orange-800">🚀 쿠팡 옵션 (조합형)</h4>
                {Object.keys(coupangOpts).length < 3 && (
                  <button
                    type="button"
                    onClick={() => {
                      const newKey = `옵션${Object.keys(coupangOpts).length + 1}`;
                      setCoupangOpts({...coupangOpts, [newKey]: ['']});
                    }}
                    className="flex items-center gap-1 px-3 py-1 bg-orange-500 text-white text-xs rounded-lg hover:bg-orange-600 transition"
                  >
                    <Plus className="w-3 h-3" />
                    옵션 추가
                  </button>
                )}
              </div>
              <p className="text-xs text-orange-600 mb-3">💡 옵션값을 쉼표(,)로 구분하여 입력하면 모든 조합이 자동 생성됩니다 (예: 1개,2개,3개)</p>
              <div className="space-y-3">
                {Object.entries(coupangOpts).map(([optName, optValues], index) => (
                  <div key={index} className="border border-orange-100 rounded-lg p-3 relative">
                    {Object.keys(coupangOpts).length > 1 && (
                      <button
                        type="button"
                        onClick={() => {
                          const newOpts = {...coupangOpts};
                          delete newOpts[optName];
                          setCoupangOpts(newOpts);
                        }}
                        className="absolute top-2 right-2 text-red-500 hover:text-red-700"
                      >
                        <Tag className="w-4 h-4" />
                      </button>
                    )}
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="text-xs text-gray-600">옵션명</label>
                        <input
                          type="text"
                          value={optName}
                          onChange={(e) => {
                            const newOpts = {...coupangOpts};
                            delete newOpts[optName];
                            newOpts[e.target.value] = optValues;
                            setCoupangOpts(newOpts);
                          }}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') e.preventDefault();
                          }}
                          className="w-full px-2 py-1 text-sm border border-orange-300 rounded focus:ring-1 focus:ring-orange-500"
                          placeholder="예: 수량"
                        />
                      </div>
                      <div>
                        <label className="text-xs text-gray-600">옵션값 (쉼표로 구분)</label>
                        <input
                          type="text"
                          value={optValues.join(',')}
                          onChange={(e) => {
                            const values = e.target.value.split(',').map(v => v.trim());
                            setCoupangOpts({...coupangOpts, [optName]: values});
                          }}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') e.preventDefault();
                          }}
                          className="w-full px-2 py-1 text-sm border border-orange-300 rounded focus:ring-1 focus:ring-orange-500"
                          placeholder="예: 1개,2개,3개"
                        />
                      </div>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      생성될 옵션: {optValues.filter(v => v).join(', ')} ({optValues.filter(v => v).length}개)
                    </p>
                  </div>
                ))}
                {Object.keys(coupangOpts).length > 1 && (
                  <div className="bg-orange-50 border border-orange-200 rounded p-2">
                    <p className="text-xs text-orange-800">
                      📦 총 {Object.values(coupangOpts).reduce((acc, vals) => acc * vals.filter(v => v).length, 1)}개 조합이 생성됩니다
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* 스마트스토어 옵션 */}
            <div className="bg-white border border-green-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-semibold text-green-800">🛒 스마트스토어 옵션 (독립형)</h4>
                {smartOpts.length < 3 && (
                  <button
                    type="button"
                    onClick={() => setSmartOpts([...smartOpts, { opt_name: '', opt_value: '', stock_cnt: 999 }])}
                    className="flex items-center gap-1 px-3 py-1 bg-green-500 text-white text-xs rounded-lg hover:bg-green-600 transition"
                  >
                    <Plus className="w-3 h-3" />
                    옵션 추가
                  </button>
                )}
              </div>
              <div className="space-y-3">
                {smartOpts.map((opt, index) => (
                  <div key={index} className="border border-green-100 rounded-lg p-3 relative">
                    {smartOpts.length > 1 && (
                      <button
                        type="button"
                        onClick={() => setSmartOpts(smartOpts.filter((_, i) => i !== index))}
                        className="absolute top-2 right-2 text-red-500 hover:text-red-700"
                      >
                        <Tag className="w-4 h-4" />
                      </button>
                    )}
                    <div className="grid grid-cols-3 gap-2">
                      <div>
                        <label className="text-xs text-gray-600">옵션명{index + 1}</label>
                        <input
                          type="text"
                          value={opt.opt_name}
                          onChange={(e) => {
                            const newOpts = [...smartOpts];
                            newOpts[index].opt_name = e.target.value;
                            setSmartOpts(newOpts);
                          }}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') e.preventDefault();
                          }}
                          className="w-full px-2 py-1 text-sm border border-green-300 rounded focus:ring-1 focus:ring-green-500"
                          placeholder={index === 0 ? "상품선택" : "옵션명"}
                        />
                      </div>
                      <div>
                        <label className="text-xs text-gray-600">옵션값{index + 1}</label>
                        <input
                          type="text"
                          value={opt.opt_value}
                          onChange={(e) => {
                            const newOpts = [...smartOpts];
                            newOpts[index].opt_value = e.target.value;
                            setSmartOpts(newOpts);
                          }}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') e.preventDefault();
                          }}
                          className="w-full px-2 py-1 text-sm border border-green-300 rounded focus:ring-1 focus:ring-green-500"
                          placeholder={index === 0 ? "상품명" : "옵션값"}
                        />
                      </div>
                      <div>
                        <label className="text-xs text-gray-600">재고</label>
                        <input
                          type="number"
                          value={opt.stock_cnt}
                          onChange={(e) => {
                            const newOpts = [...smartOpts];
                            newOpts[index].stock_cnt = parseInt(e.target.value) || 999;
                            setSmartOpts(newOpts);
                          }}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') e.preventDefault();
                          }}
                          className="w-full px-2 py-1 text-sm border border-green-300 rounded focus:ring-1 focus:ring-green-500"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* 배송비 설정 */}
          <div className="bg-white border border-blue-200 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-blue-800 mb-3">🚚 배송비 설정</h4>
            <div className="space-y-3">
              <div className="flex gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="ship_price_type"
                    value="선결제"
                    checked={formData.ship_price_type === '선결제'}
                    onChange={(e) => setFormData({ ...formData, ship_price_type: e.target.value as '선결제' | '무료' })}
                    className="w-4 h-4 text-blue-600"
                  />
                  <span className="text-sm text-gray-700">선결제</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="ship_price_type"
                    value="무료"
                    checked={formData.ship_price_type === '무료'}
                    onChange={(e) => setFormData({ ...formData, ship_price_type: e.target.value as '선결제' | '무료' })}
                    className="w-4 h-4 text-blue-600"
                  />
                  <span className="text-sm text-gray-700">무료배송</span>
                </label>
              </div>
              {formData.ship_price_type === '선결제' && (
                <div>
                  <label className="text-xs text-gray-600">배송비 (원)</label>
                  <input
                    type="number"
                    value={formData.ship_price}
                    onChange={(e) => setFormData({ ...formData, ship_price: e.target.value })}
                    className="w-full px-3 py-2 text-sm border border-blue-300 rounded-lg focus:ring-1 focus:ring-blue-500"
                    placeholder="3000"
                  />
                </div>
              )}
            </div>
          </div>

          {/* 소싱 정보 */}
          {formData.sourcing_url && (
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 space-y-2">
              <div className="text-sm font-semibold text-purple-800">소싱 정보</div>
              <div className="text-sm text-gray-700">
                <div><span className="font-medium">마켓:</span> {detectedSource}</div>
                {formData.sourcing_price && (
                  <div><span className="font-medium">소싱가:</span> {parseInt(formData.sourcing_price).toLocaleString()}원</div>
                )}
                <div className="truncate"><span className="font-medium">URL:</span> {formData.sourcing_url}</div>
              </div>
            </div>
          )}

          {/* 상세페이지 정보 */}
          <div className="bg-gradient-to-r from-purple-50 to-pink-50 border-2 border-purple-200 rounded-lg p-4">
            <div className="flex items-center gap-2 text-sm font-semibold text-purple-800 mb-2">
              <CheckCircle className="w-4 h-4" />
              상세페이지 자동 포함
            </div>
            <div className="text-sm text-gray-700">
              현재 생성한 상세페이지가 이 상품에 자동으로 연결됩니다.
            </div>
          </div>

          {/* 검색 키워드 */}
          {isGeneratingKeywords ? (
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-300 rounded-xl p-5">
              <div className="flex items-center justify-center gap-2 py-8">
                <RefreshCw className="w-5 h-5 text-blue-600 animate-spin" />
                <span className="text-blue-600 font-medium">AI가 키워드를 생성하는 중...</span>
              </div>
            </div>
          ) : (
            <KeywordEditor
              keywords={keywords}
              onKeywordsChange={setKeywords}
              productName={formData.product_name}
              category={`${category.level1} > ${category.level2} > ${category.level3} > ${category.level4}`}
              disabled={loading}
            />
          )}

          {/* 메모 */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">메모</label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              rows={3}
              placeholder="상품에 대한 메모를 입력하세요"
            />
          </div>

          <div className="flex gap-3">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-600 text-white rounded-xl font-semibold hover:shadow-lg transition-all disabled:opacity-50"
            >
              {loading ? '등록 중...' : '상품 등록'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-3 bg-gray-500 text-white rounded-xl font-semibold hover:bg-gray-600 transition-colors"
            >
              취소
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
