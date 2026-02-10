import { categoryIdMapping } from './categories';
import type { Category } from '@/types';
import { adminGet } from './adminApi';

class ImageService {
  private static instance: ImageService;

  static getInstance(): ImageService {
    if (!ImageService.instance) {
      ImageService.instance = new ImageService();
    }
    return ImageService.instance;
  }

  async getImagesFromFolder(folderId: string): Promise<string[]> {
    try {
      // Admin API의 gallery 엔드포인트 사용 (인증 헤더 자동 추가)
      const data = await adminGet<{ success: boolean; images?: any[] }>(`/api/admin/images/gallery/${folderId}`);

      if (!data.success || !data.images) {
        console.warn(`Invalid response for folder ${folderId}`);
        return [];
      }

      // 백엔드 API가 이미 공개 URL을 반환하므로 그대로 사용
      // Supabase Storage URL: https://{project}.supabase.co/storage/v1/object/public/product-images/cat-{id}/{filename}
      const imageUrls = data.images.map((img: any) => img.path);

      console.log(`[ImageService] Loaded ${imageUrls.length} images from folder ${folderId}`);

      return imageUrls;
    } catch (error) {
      console.error('Error in getImagesFromFolder:', error);
      return [];
    }
  }

  shuffleArray<T>(array: T[]): T[] {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
  }

  async getAutoImages(category: Category): Promise<Record<string, string>> {
    const { level4 } = category;
    const folderId = categoryIdMapping[level4];

    if (!folderId) {
      console.error(`No folder mapping for category: ${level4}`);
      return {};
    }

    const images = await this.getImagesFromFolder(folderId);

    if (images.length === 0) {
      console.warn(`No images found in folder ${folderId}`);
      return {};
    }

    const shuffled = this.shuffleArray(images);
    const imageKeys = [
      // 템플릿A (Daily)
      'template1_bg', 'template2_main', 'template2_sub', 'template4_bg',
      'template5_pt1', 'template5_pt2', 'template5_pt3', 'template5_pt4',
      'template6_bg', 'template6_additional',
      // 템플릿B (Food/Convenience)
      'food_template1_bg', 'food_template2_main', 'food_review1', 'food_review2', 'food_review3',
      'food_product_image', 'food_template5_main', 'food_template5_additional',
      // 전자제품류, 가공식품류, 위생용품류, 문구류 (공통 키)
      'intro_main', 'feature1_image', 'feature2_bg', 'feature3_image', 'feature4_image1'
    ];

    const result: Record<string, string> = {};
    imageKeys.forEach((key, index) => {
      if (index < shuffled.length) {
        result[key] = shuffled[index];
      } else {
        result[key] = shuffled[index % shuffled.length];
      }
    });

    return result;
  }

  getFolderPath(categoryName: string): string | null {
    return categoryIdMapping[categoryName] || null;
  }
}

export const imageService = ImageService.getInstance();
