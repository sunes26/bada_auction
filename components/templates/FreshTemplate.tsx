import { Star, Leaf } from 'lucide-react';
import EditableText from './EditableText';
import EditableImage from './EditableImage';
import { TemplateProps } from './TemplateProps';

export default function FreshTemplate(props: TemplateProps) {
  const { content, uploadedImages, editingField, editingValue, onImageUpload, onImageRefresh, onImageDrop, onTextEdit, onTextSave, onTextCancel, onValueChange, onImageClick, editingImage, imageStyleSettings, onImageDelete, onTextStyleClick, textStyles = {}, additionalImageSlots = 0, onAddImageSlot, onRemoveImageSlot, imageSizes = {}, onImageResize, imagePositions = {}, onImageMove, imageAlignments = {}, onImageAlignment } = props;

  return (
    <>
      {/* Hero Section - 초록 배지 + 제품명 + 이미지 + 잎 장식 */}
      <div className="w-full bg-gradient-to-b from-green-50 to-white py-16 px-10 text-center relative">
        {/* 초록 잎 장식 - 좌상단 */}
        <div className="absolute top-8 left-8">
          <Leaf className="w-16 h-16 text-green-500 transform -rotate-45" />
        </div>

        {/* 초록 배지 */}
        <div className="inline-block bg-green-500 text-white px-6 py-2 rounded-full text-lg font-bold mb-6">
          <EditableText field="subtitle" value={content.subtitle} editingField={editingField} editingValue={editingValue} onEdit={onTextEdit} onSave={onTextSave} onCancel={onTextCancel} onValueChange={onValueChange} onStyleClick={onTextStyleClick} textStyles={textStyles} />
        </div>

        {/* 제품 이미지 */}
        <div className="max-w-2xl mx-auto mb-8">
          <EditableImage imageKey="fresh_template1_main" uploadedImages={uploadedImages} className="w-full h-[500px] rounded-3xl shadow-2xl" onImageUpload={onImageUpload} onImageRefresh={onImageRefresh}
          onImageDrop={onImageDrop} onImageClick={onImageClick} editingImage={editingImage} imageStyleSettings={imageStyleSettings} onImageDelete={onImageDelete} imageSizes={imageSizes} onImageResize={onImageResize} imagePositions={imagePositions} onImageMove={onImageMove} imageAlignments={imageAlignments} onImageAlignment={onImageAlignment} fillContainer={true} isResizable={false} />
        </div>
      </div>

      {/* 설명 + 이미지 + 3개 원형 아이콘 Section */}
      <div className="w-full bg-white py-20 px-10">
        <div className="max-w-5xl mx-auto">
          {/* 빨간 텍스트 */}
          <p className="text-center text-2xl text-red-500 font-semibold mb-12 leading-relaxed">
            <EditableText field="productDescription1" value={content.productDescription1} editingField={editingField} editingValue={editingValue} onEdit={onTextEdit} onSave={onTextSave} onCancel={onTextCancel} onValueChange={onValueChange} onStyleClick={onTextStyleClick} textStyles={textStyles} />
          </p>

          {/* 이미지 + 100% 황금 배지 */}
          <div className="relative max-w-3xl mx-auto mb-12">
            <EditableImage imageKey="fresh_template1_sub" uploadedImages={uploadedImages} className="w-full h-[500px] rounded-2xl shadow-xl" onImageUpload={onImageUpload} onImageRefresh={onImageRefresh}
          onImageDrop={onImageDrop} onImageClick={onImageClick} editingImage={editingImage} imageStyleSettings={imageStyleSettings} onImageDelete={onImageDelete} imageSizes={imageSizes} onImageResize={onImageResize} imagePositions={imagePositions} onImageMove={onImageMove} imageAlignments={imageAlignments} onImageAlignment={onImageAlignment} fillContainer={true} isResizable={false} />

            {/* 100% 황금 배지 - 우상단 */}
            <div className="absolute top-4 right-4">
              <div className="bg-gradient-to-br from-yellow-400 to-yellow-600 text-black w-24 h-24 rounded-full flex items-center justify-center font-bold text-2xl shadow-2xl border-4 border-yellow-300">
                <EditableText
                  field="goldBadgeText"
                  value={content.goldBadgeText || '100%'}
                  editingField={editingField}
                  editingValue={editingValue}
                  onEdit={onTextEdit}
                  onSave={onTextSave}
                  onCancel={onTextCancel}
                  onValueChange={onValueChange}
                  onStyleClick={onTextStyleClick}
                  textStyles={textStyles}
                />
              </div>
            </div>
          </div>

          {/* 3개 원형 아이콘 - 흰 배경 + 분홍 테두리 */}
          <div className="flex justify-center gap-12">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex flex-col items-center">
                <div className="w-24 h-24 rounded-full bg-white border-4 border-pink-400 flex items-center justify-center mb-4 shadow-lg">
                  <span className="text-3xl">
                    <EditableText field={`tag${i}`} value={content[`tag${i}`]} editingField={editingField} editingValue={editingValue} onEdit={onTextEdit} onSave={onTextSave} onCancel={onTextCancel} onValueChange={onValueChange} onStyleClick={onTextStyleClick} textStyles={textStyles} />
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 검정 배경 - 최고급 원유 + 가격 + 평점 */}
      <div className="w-full bg-black text-white py-20 px-10 text-center">
        {/* 황금 배지 */}
        <div className="inline-block relative mb-8">
          <div className="bg-gradient-to-br from-yellow-400 to-yellow-600 text-black px-8 py-4 rounded-full font-bold text-2xl shadow-2xl">
            <EditableText field="coreMessage1" value={content.coreMessage1 || "최고급 원유"} editingField={editingField} editingValue={editingValue} onEdit={onTextEdit} onSave={onTextSave} onCancel={onTextCancel} onValueChange={onValueChange} onStyleClick={onTextStyleClick} textStyles={textStyles} />
          </div>
        </div>

        {/* 가격 정보 */}
        <div className="max-w-md mx-auto bg-white text-black rounded-2xl p-8 mb-8">
          <h3 className="text-4xl font-bold mb-4">
            <EditableText field="priceTitle" value={content.priceTitle || "노력대비행"} editingField={editingField} editingValue={editingValue} onEdit={onTextEdit} onSave={onTextSave} onCancel={onTextCancel} onValueChange={onValueChange} onStyleClick={onTextStyleClick} textStyles={textStyles} />
          </h3>
          <p className="text-5xl font-extrabold text-red-600">
            <EditableText field="price" value={content.price || "20,000원"} editingField={editingField} editingValue={editingValue} onEdit={onTextEdit} onSave={onTextSave} onCancel={onTextCancel} onValueChange={onValueChange} onStyleClick={onTextStyleClick} textStyles={textStyles} />
          </p>
        </div>

        {/* 평점 */}
        <div className="max-w-md mx-auto bg-white text-black rounded-2xl p-6">
          <div className="flex justify-center mb-2">
            {[1, 2, 3, 4, 5].map((i) => (
              <Star key={i} className="w-6 h-6 fill-yellow-400 text-yellow-400" />
            ))}
          </div>
          <p className="text-3xl font-bold">
            <EditableText field="rating" value={content.rating || "평점 4.8점"} editingField={editingField} editingValue={editingValue} onEdit={onTextEdit} onSave={onTextSave} onCancel={onTextCancel} onValueChange={onValueChange} onStyleClick={onTextStyleClick} textStyles={textStyles} />
          </p>
        </div>
      </div>

      {/* 장점 Section - 검정 배경 */}
      <div className="w-full bg-black text-white py-20 px-10 text-center">
        <h2 className="text-4xl font-bold mb-12">
          <EditableText
            field="advantageTitle"
            value={content.advantageTitle || '장점'}
            editingField={editingField}
            editingValue={editingValue}
            onEdit={onTextEdit}
            onSave={onTextSave}
            onCancel={onTextCancel}
            onValueChange={onValueChange}
            onStyleClick={onTextStyleClick}
            textStyles={textStyles}
          />
        </h2>
        <div className="max-w-4xl mx-auto">
          <EditableImage imageKey="fresh_point1" uploadedImages={uploadedImages} className="w-full h-[500px] rounded-2xl shadow-2xl" onImageUpload={onImageUpload} onImageRefresh={onImageRefresh}
          onImageDrop={onImageDrop} onImageClick={onImageClick} editingImage={editingImage} imageStyleSettings={imageStyleSettings} onImageDelete={onImageDelete} imageSizes={imageSizes} onImageResize={onImageResize} imagePositions={imagePositions} onImageMove={onImageMove} imageAlignments={imageAlignments} onImageAlignment={onImageAlignment} fillContainer={true} isResizable={false} />
        </div>
      </div>

      {/* 분홍 배지 Section 1 - 아침 커피의 단짝 */}
      <div className="w-full bg-white py-20 px-10">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <span className="inline-block bg-pink-500 text-white px-8 py-3 rounded-full font-bold text-xl">
              <EditableText field="freshPoint1Title" value={content.freshPoint1Title || "아침 커피의 단짝"} editingField={editingField} editingValue={editingValue} onEdit={onTextEdit} onSave={onTextSave} onCancel={onTextCancel} onValueChange={onValueChange} onStyleClick={onTextStyleClick} textStyles={textStyles} />
            </span>
          </div>
          <p className="text-center text-xl text-gray-700 mb-8">
            <EditableText field="freshPoint1Description" value={content.freshPoint1Description} editingField={editingField} editingValue={editingValue} onEdit={onTextEdit} onSave={onTextSave} onCancel={onTextCancel} onValueChange={onValueChange} onStyleClick={onTextStyleClick} textStyles={textStyles} />
          </p>
          <EditableImage imageKey="fresh_point2" uploadedImages={uploadedImages} className="w-full h-[500px] rounded-2xl shadow-xl" onImageUpload={onImageUpload} onImageRefresh={onImageRefresh}
          onImageDrop={onImageDrop} onImageClick={onImageClick} editingImage={editingImage} imageStyleSettings={imageStyleSettings} onImageDelete={onImageDelete} imageSizes={imageSizes} onImageResize={onImageResize} imagePositions={imagePositions} onImageMove={onImageMove} imageAlignments={imageAlignments} onImageAlignment={onImageAlignment} fillContainer={true} isResizable={false} />
        </div>
      </div>

      {/* 분홍 배지 Section 2 - 면역 개선에 탁월 */}
      <div className="w-full bg-white py-20 px-10">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <span className="inline-block bg-pink-500 text-white px-8 py-3 rounded-full font-bold text-xl">
              <EditableText field="freshPoint2Title" value={content.freshPoint2Title || "면역 개선에 탁월"} editingField={editingField} editingValue={editingValue} onEdit={onTextEdit} onSave={onTextSave} onCancel={onTextCancel} onValueChange={onValueChange} onStyleClick={onTextStyleClick} textStyles={textStyles} />
            </span>
          </div>
          <p className="text-center text-xl text-gray-700 mb-8">
            <EditableText field="freshPoint2Description" value={content.freshPoint2Description} editingField={editingField} editingValue={editingValue} onEdit={onTextEdit} onSave={onTextSave} onCancel={onTextCancel} onValueChange={onValueChange} onStyleClick={onTextStyleClick} textStyles={textStyles} />
          </p>
          <EditableImage imageKey="fresh_point3" uploadedImages={uploadedImages} className="w-full h-[500px] rounded-2xl shadow-xl" onImageUpload={onImageUpload} onImageRefresh={onImageRefresh}
          onImageDrop={onImageDrop} onImageClick={onImageClick} editingImage={editingImage} imageStyleSettings={imageStyleSettings} onImageDelete={onImageDelete} imageSizes={imageSizes} onImageResize={onImageResize} imagePositions={imagePositions} onImageMove={onImageMove} imageAlignments={imageAlignments} onImageAlignment={onImageAlignment} fillContainer={true} isResizable={false} />
        </div>
      </div>

      {/* 분홍 배지 Section 3 - 비타민 풍부 보장 */}
      <div className="w-full bg-white py-20 px-10">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <span className="inline-block bg-pink-500 text-white px-8 py-3 rounded-full font-bold text-xl">
              <EditableText field="freshPoint3Title" value={content.freshPoint3Title || "비타민 풍부 보장"} editingField={editingField} editingValue={editingValue} onEdit={onTextEdit} onSave={onTextSave} onCancel={onTextCancel} onValueChange={onValueChange} onStyleClick={onTextStyleClick} textStyles={textStyles} />
            </span>
          </div>
          <p className="text-center text-xl text-gray-700 mb-8">
            <EditableText field="freshPoint3Description" value={content.freshPoint3Description} editingField={editingField} editingValue={editingValue} onEdit={onTextEdit} onSave={onTextSave} onCancel={onTextCancel} onValueChange={onValueChange} onStyleClick={onTextStyleClick} textStyles={textStyles} />
          </p>
          <EditableImage imageKey="fresh_composition_image" uploadedImages={uploadedImages} className="w-full h-[500px] rounded-2xl shadow-xl" onImageUpload={onImageUpload} onImageRefresh={onImageRefresh}
          onImageDrop={onImageDrop} onImageClick={onImageClick} editingImage={editingImage} imageStyleSettings={imageStyleSettings} onImageDelete={onImageDelete} imageSizes={imageSizes} onImageResize={onImageResize} imagePositions={imagePositions} onImageMove={onImageMove} imageAlignments={imageAlignments} onImageAlignment={onImageAlignment} fillContainer={true} isResizable={false} />
        </div>
      </div>

      {/* 주의사항 Section - 연한 초록 배경 */}
      <div className="w-full bg-green-50 py-16 px-10">
        <div className="max-w-4xl mx-auto text-center">
          <div className="flex items-center justify-center gap-2 mb-6">
            <Leaf className="w-6 h-6 text-green-600" />
            <h3 className="text-2xl font-bold text-gray-800">
              <EditableText
                field="cautionLabel"
                value={content.cautionLabel || '주의사항'}
                editingField={editingField}
                editingValue={editingValue}
                onEdit={onTextEdit}
                onSave={onTextSave}
                onCancel={onTextCancel}
                onValueChange={onValueChange}
                onStyleClick={onTextStyleClick}
                textStyles={textStyles}
              />
            </h3>
          </div>
          <p className="text-lg text-gray-700 leading-relaxed whitespace-pre-wrap">
            <EditableText field="cautionContent" value={content.cautionContent} isTextarea editingField={editingField} editingValue={editingValue} onEdit={onTextEdit} onSave={onTextSave} onCancel={onTextCancel} onValueChange={onValueChange} onStyleClick={onTextStyleClick} textStyles={textStyles} />
          </p>
        </div>
      </div>

      {/* 상품 구성 체크리스트 Section */}
      <div className="w-full bg-white py-20 px-10">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-4xl font-bold text-center text-gray-800 mb-12">
            <EditableText
              field="compositionTitle"
              value={content.compositionTitle || '상품 구성'}
              editingField={editingField}
              editingValue={editingValue}
              onEdit={onTextEdit}
              onSave={onTextSave}
              onCancel={onTextCancel}
              onValueChange={onValueChange}
              onStyleClick={onTextStyleClick}
              textStyles={textStyles}
            />
          </h2>

          {/* 체크리스트 */}
          <div className="bg-green-50 rounded-2xl p-8 mb-8">
            <ul className="space-y-4">
              {[1, 2, 3].map((i) => (
                <li key={i} className="flex items-center gap-3">
                  <span className="text-green-600 text-2xl">✓</span>
                  <span className="text-lg text-gray-700">
                    <EditableText field={`checkItem${i}`} value={content[`checkItem${i}`] || `No.0${i}내용`} editingField={editingField} editingValue={editingValue} onEdit={onTextEdit} onSave={onTextSave} onCancel={onTextCancel} onValueChange={onValueChange} onStyleClick={onTextStyleClick} textStyles={textStyles} />
                  </span>
                </li>
              ))}
            </ul>
          </div>

          {/* 이미지 */}
          <EditableImage imageKey="fresh_template2_main" uploadedImages={uploadedImages} className="w-full h-[400px] rounded-2xl shadow-xl" onImageUpload={onImageUpload} onImageRefresh={onImageRefresh}
          onImageDrop={onImageDrop} onImageClick={onImageClick} editingImage={editingImage} imageStyleSettings={imageStyleSettings} onImageDelete={onImageDelete} imageSizes={imageSizes} onImageResize={onImageResize} imagePositions={imagePositions} onImageMove={onImageMove} imageAlignments={imageAlignments} onImageAlignment={onImageAlignment} fillContainer={true} isResizable={false} />

          {/* 추가 이미지 슬롯 */}
          {Array.from({ length: additionalImageSlots }).map((_, index) => (
            <div key={index} className="relative mt-6">
              <EditableImage
                imageKey={`additional_product_image_${index}`}
                uploadedImages={uploadedImages}
                className="w-full h-[400px] rounded-2xl shadow-xl"
                onImageUpload={onImageUpload}
                onImageRefresh={onImageRefresh}
                onImageDrop={onImageDrop}
                onImageClick={onImageClick}
                editingImage={editingImage}
                imageStyleSettings={imageStyleSettings}
                onImageDelete={onImageDelete}
                imageSizes={imageSizes}
                onImageResize={onImageResize}
                imagePositions={imagePositions}
                onImageMove={onImageMove}
                fillContainer={false}
                isResizable={true}
              />
              {onRemoveImageSlot && (
                <button
                  onClick={() => onRemoveImageSlot(index)}
                  className="absolute top-2 left-2 w-8 h-8 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 transition-colors shadow-lg z-10"
                  title="이미지 슬롯 삭제"
                >
                  ×
                </button>
              )}
            </div>
          ))}

          {/* + 버튼 */}
          {onAddImageSlot && (
            <div className="flex justify-center mt-6">
              <button
                onClick={onAddImageSlot}
                className="w-16 h-16 bg-gray-200 hover:bg-gray-300 rounded-full flex items-center justify-center text-gray-600 hover:text-gray-800 transition-colors shadow-md"
                title="이미지 추가"
              >
                <span className="text-4xl font-light">+</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
