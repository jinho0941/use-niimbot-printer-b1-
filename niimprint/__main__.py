import asyncio
import serial
import struct
from PIL import Image, ImageOps
import math
from serial.tools.list_ports import comports


class NiimbotPacket:
    def __init__(self, type_, data):
        self.type = type_
        self.data = data

    @classmethod
    def from_bytes(cls, pkt):
        if not pkt or len(pkt) < 7:  # 최소 패킷 길이 검증
            return None
        if not (pkt[:2] == b"\x55\x55" and pkt[-2:] == b"\xaa\xaa"):
            return None

        type_ = pkt[2]
        len_ = pkt[3]
        data = pkt[4:4 + len_]

        # 체크섬 검증
        checksum = type_ ^ len_
        for i in data:
            checksum ^= i
        if checksum != pkt[-3]:
            return None

        return cls(type_, data)

    def to_bytes(self):
        checksum = self.type ^ len(self.data)
        for i in self.data:
            checksum ^= i
        return bytes((0x55, 0x55, self.type, len(self.data), *self.data, checksum, 0xAA, 0xAA))


async def main():
    # 자동 포트 감지
    ports = list(comports())
    if not ports:
        print("프린터를 찾을 수 없습니다")
        return
    port = ports[0].device

    # 시리얼 연결
    ser = serial.Serial(port=port, baudrate=115200, timeout=1)

    async def send_packet(type_, data, retry=3):
        packet = NiimbotPacket(type_, data)
        pkt_bytes = packet.to_bytes()

        for _ in range(retry):
            ser.write(pkt_bytes)
            await asyncio.sleep(0.2)  # 응답 대기 시간 증가

            resp = ser.read(1024)
            if resp:
                resp_packet = NiimbotPacket.from_bytes(resp)
                if resp_packet:
                    return resp_packet
        return None

    # 프린터 상태 확인
    status = await send_packet(220, b"\x01")  # HEARTBEAT
    if status and status.data:
        print("\n프린터 상태:")
        if len(status.data) >= 13:
            print(f"전원 레벨: {status.data[10]}%")
            print(f"용지 상태: {'정상' if status.data[11] == 0 else '용지 없음'}")
            print(f"RFID 상태: {'정상' if status.data[12] == 0 else '오류'}")

    # 이미지 로드 및 전처리
    image = Image.open("./qr.png")
    img = ImageOps.invert(image.convert("L")).convert("1")

    # 3개 연속 인쇄
    for i in range(3):
        print(f"\n{i + 1}번째 인쇄 시작")

        # 초기화 및 설정
        await send_packet(33, bytes((3,)))  # density
        await send_packet(35, bytes((1,)))  # label type
        await send_packet(1, b"\x01")  # start print
        await send_packet(3, b"\x01")  # start page

        # 크기 설정
        await send_packet(19, struct.pack(">HH", img.height, img.width))

        # 이미지 데이터 전송
        for y in range(img.height):
            line_data = [img.getpixel((x, y)) for x in range(img.width)]
            line_bytes = "".join("0" if pix == 0 else "1" for pix in line_data)
            line_bytes = int(line_bytes, 2).to_bytes(math.ceil(img.width / 8), "big")
            header = struct.pack(">H3BB", y, 0, 0, 0, 1)
            await send_packet(0x85, header + line_bytes)

        await send_packet(227, b"\x01")  # end page
        await asyncio.sleep(0.5)

        # 인쇄 완료 대기
        while True:
            resp = await send_packet(243, b"\x01")  # END_PRINT
            if resp and resp.data and resp.data[0]:
                break
            await asyncio.sleep(0.2)

        print(f"{i + 1}번째 인쇄 완료")


if __name__ == "__main__":
    asyncio.run(main())