from niimprint import SerialTransport, PrinterClient
import time
import logging

class NiimbotPrinter:
    def __init__(self, port="auto"):
        try:
            transport = SerialTransport(port=port)
            self.printer = PrinterClient(transport)
        except Exception as e:
            logging.error(f"프린터 초기화 실패: {str(e)}")
            raise

        # 로깅 설정
        logging.basicConfig(
            format="%(asctime)s | ERROR | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    def check_status(self):
        """프린터 상태 확인"""
        try:
            status = self.printer.heartbeat()
            print_status = self.printer.get_print_status()
        except Exception as e:
            logging.error(f"프린터 상태 확인 실패: {str(e)}")
            return {}

        status_info = {
            "battery": status.get("powerlevel"),
            "paper": status.get("paperstate"),
            "rfid": status.get("rfidreadstate")
        }

        if print_status:
            status_info.update({
                "page": print_status.get("page"),
                "progress": print_status.get("progress1"),
                "state": print_status.get("state1"),
                "enabled": print_status.get("isEnabled")
            })

        return status_info

    def get_printer_condition(self):
        """배터리 레벨과 프린터 활성화 상태 반환"""
        try:
            status = self.check_status()
            return {
                "battery_level": status.get("battery"),
                "is_enabled": status.get("enabled", False)
            }
        except Exception as e:
            logging.error(f"프린터 상태 조회 실패: {str(e)}")
            return {"battery_level": 0, "is_enabled": False}

    def is_printer_available(self):
        """프린터 사용 가능 여부 확인"""
        try:
            status = self.check_status()
            battery = status.get("battery", 0)
            paper = status.get("paper")
            enabled = status.get("enabled", False)

            # 배터리 부족
            if battery <= 1:
                logging.error(f"배터리 부족 - 현재 배터리: {battery}")
                return False

            # 용지 없음
            if paper == 1:
                logging.error("용지 없음")
                return False

            # 프린터 비활성화
            if not enabled:
                logging.error("프린터가 비활성화 상태")
                return False

            return True

        except Exception as e:
            logging.error(f"프린터 상태 확인 실패: {str(e)}")
            return False

    def print_qr_image(self, image, count=1):
        """QR 코드 이미지 인쇄"""
        if not self.is_printer_available():
            return

        try:
            self.printer.set_label_density(3)
            self.printer.set_label_type(1)

            for i in range(count):
                print(f"\n{i + 1}번째 인쇄 시작")
                self.printer.start_print()
                self.printer.start_page_print()
                self.printer.set_dimension(image.height, image.width)
                self.printer.print_image(image)

                while not self.printer.end_print():
                    status = self.check_status()
                    print(f"진행률: {status.get('progress')}%")
                    time.sleep(0.1)
        except Exception as e:
            logging.error(f"QR 코드 인쇄 실패: {str(e)}")