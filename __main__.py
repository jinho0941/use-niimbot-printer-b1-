from src.niimbot_printer import NiimbotPrinter
from src.qr_generator import QRGenerator
import logging

if __name__ == "__main__":
    try:
        # 내용 기반 QR 코드 생성
        text = "test1234"
        qr_generator = QRGenerator()
        qr_image = qr_generator.generate_qr_image(text)

        # 프린터 초기화 및 인쇄
        printer = NiimbotPrinter()

        if not printer.is_printer_available():
            raise RuntimeError("프린터를 사용할 수 없습니다")

        condition = printer.get_printer_condition()
        print("프린터 상태:", condition)

        printer.print_qr_image(qr_image, 2)
        qr_image.close()  # 이미지 메모리 해제

    except Exception as e:
        logging.error(f"프로그램 실행 중 오류 발생: {str(e)}")
        exit(1)