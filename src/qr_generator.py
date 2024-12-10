from PIL import Image
import qrcode
import logging

class QRGenerator:
    def __init__(self):
        self.qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

    def generate_qr_image(self, data):
        """QR 코드 이미지 생성"""
        try:
            # QR 코드 생성
            self.qr.clear()  # 이전 데이터 초기화
            self.qr.add_data(data)
            self.qr.make(fit=True)
            qr_img = self.qr.make_image(fill_color="black", back_color="white")

            # 배경 이미지 생성 및 QR 코드 배치
            background = Image.new('RGB', (320, 240), 'white')

            # 상하 여백 10px을 고려한 QR 크기 계산
            vertical_padding = 20  # 상하 각각 10px
            qr_size = min(240 - vertical_padding, 320)  # 전체 높이에서 패딩 크기를 뺀 값과 너비 중 작은 값
            qr_resized = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)

            # 가로 중앙, 세로는 10px 패딩 적용
            x_offset = (320 - qr_size) // 2
            y_offset = (240 - qr_size) // 2  # 중앙 정렬
            y_offset = 10 + ((240 - 20 - qr_size) // 2)  # 상하 패딩 10px 적용

            background.paste(qr_resized, (x_offset, y_offset))

            return background
        except Exception as e:
            logging.error(f"QR 코드 이미지 생성 실패: {str(e)}")
            raise