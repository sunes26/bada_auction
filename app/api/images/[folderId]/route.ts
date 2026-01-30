import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ folderId: string }> | { folderId: string } }
) {
  try {
    // Next.js 15+ params는 Promise일 수 있음
    const resolvedParams = await Promise.resolve(params);
    const { folderId } = resolvedParams;

    console.log('[API] Fetching images for folderId:', folderId);

    // supabase-images 폴더에서 [숫자]_[이름] 형식의 폴더 찾기
    const baseDir = path.join(process.cwd(), 'supabase-images');

    if (!fs.existsSync(baseDir)) {
      return NextResponse.json([], { status: 200 });
    }

    // 모든 폴더 목록 읽기
    const allFolders = fs.readdirSync(baseDir);

    // folderId로 시작하는 폴더 찾기 (예: "1_흰밥", "10_치킨마요")
    const targetFolder = allFolders.find(folder => {
      // "숫자_이름" 형식에서 숫자 부분 추출
      const folderNum = folder.split('_')[0];
      return folderNum === folderId;
    });

    if (!targetFolder) {
      return NextResponse.json([], { status: 200 });
    }

    const imagesDir = path.join(baseDir, targetFolder);

    // 폴더 내의 파일 목록 읽기
    const files = fs.readdirSync(imagesDir);

    // 이미지 파일만 필터링
    const imageFiles = files.filter(file => {
      const ext = path.extname(file).toLowerCase();
      return ['.jpg', '.jpeg', '.png', '.webp', '.gif'].includes(ext);
    });

    // 파일명에 폴더 경로 포함해서 반환 (supabase-images/1_흰밥/image.jpg)
    const imageFilesWithPath = imageFiles.map(file => `${targetFolder}/${file}`);

    return NextResponse.json(imageFilesWithPath, { status: 200 });
  } catch (error) {
    console.error('Error reading images directory:', error);
    return NextResponse.json([], { status: 200 });
  }
}
