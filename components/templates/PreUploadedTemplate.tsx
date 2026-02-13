import { TemplateProps } from './TemplateProps';

export default function PreUploadedTemplate(props: TemplateProps) {
  const {
    uploadedImages,
  } = props;

  // 업로드된 상세페이지 이미지 표시
  const detailPageImage = uploadedImages['detail_page'];

  if (!detailPageImage) {
    return (
      <div className="w-full min-h-[600px] flex items-center justify-center bg-gray-100">
        <p className="text-gray-500 text-lg">상세페이지 이미지를 업로드해주세요</p>
      </div>
    );
  }

  return (
    <div className="w-full">
      <img
        src={detailPageImage}
        alt="상세페이지"
        className="w-full h-auto"
      />
    </div>
  );
}
