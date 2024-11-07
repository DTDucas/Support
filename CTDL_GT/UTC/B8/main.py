from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Tuple, Protocol
from dataclasses import dataclass
from enum import Enum

@dataclass
class CuocGoi:
    so_phut: int
    thoi_diem: str
    ngay: str
    vung: str

@dataclass
class KhachHang:
    ten: str
    so_dt: str
    cuoc_goi: List[CuocGoi]

class VungGoi(Enum):
    NH = "NH"
    LC = "LC"
    X = "X" 
    RX = "RX"

class IFileReader(Protocol):
    def read(self, file_path: str) -> List[str]:
        pass

class IFileWriter(Protocol):
    def write(self, file_path: str, content: List[str]) -> None:
        pass

class TextFileHandler:
    def read(self, file_path: str) -> List[str]:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.readlines()

    def write(self, file_path: str, content: List[str]) -> None:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(content)

class KhachHangRepository:
    def __init__(self, file_handler: IFileReader):
        self.file_handler = file_handler

    def load_khach_hang(self, file_path: str) -> Dict[str, KhachHang]:
        khach_hang_dict = {}
        lines = self.file_handler.read(file_path)
        for line in lines:
            ten, so_dt = line.strip().split(';')
            khach_hang_dict[so_dt.strip()] = KhachHang(
                ten.strip(), 
                so_dt.strip(), 
                []
            )
        return khach_hang_dict

class CuocGoiRepository:
    def __init__(self, file_handler: IFileReader):
        self.file_handler = file_handler

    def load_cuoc_goi(self, file_path: str, khach_hang_dict: Dict[str, KhachHang]) -> None:
        lines = self.file_handler.read(file_path)
        for line in lines:
            so_dt, so_phut, thoi_diem, ngay, vung = line.strip().split(';')
            so_dt = so_dt.strip()
            if so_dt in khach_hang_dict:
                cuoc_goi = CuocGoi(
                    int(so_phut),
                    thoi_diem.strip(),
                    ngay.strip(),
                    vung.strip()
                )
                khach_hang_dict[so_dt].cuoc_goi.append(cuoc_goi)

class GiamGiaService:
    @staticmethod
    def kiem_tra_giam_gia(thoi_diem: str, ngay: str) -> bool:
        gio = int(thoi_diem.split('h')[0])
        ngay_dt = datetime.strptime(ngay, '%d/%m/%Y')
        
        if 23 <= gio or gio <= 5:
            return True
        
        if ngay_dt.weekday() >= 5:
            return True
        
        return False

class TinhCuocService:
    GIA_CO_BAN = 1100
    HE_SO_MIEN = {
        VungGoi.NH.value: 1,
        VungGoi.LC.value: 2,
        VungGoi.X.value: 3,
        VungGoi.RX.value: 4
    }

    def __init__(self, giam_gia_service: GiamGiaService):
        self.giam_gia_service = giam_gia_service

    def tinh_tien_cuoc_goi(self, cuoc_goi: CuocGoi) -> float:
        tien = self.GIA_CO_BAN * cuoc_goi.so_phut * self.HE_SO_MIEN[cuoc_goi.vung]
        
        if self.giam_gia_service.kiem_tra_giam_gia(cuoc_goi.thoi_diem, cuoc_goi.ngay):
            tien *= 0.7
        
        return tien

class ThongKeService:
    def dem_cuoc_goi_theo_vung(self, cuoc_goi_list: List[CuocGoi]) -> Dict[str, int]:
        thong_ke = {vung.value: 0 for vung in VungGoi}
        for cuoc_goi in cuoc_goi_list:
            thong_ke[cuoc_goi.vung] += 1
        return thong_ke

class BaoCaoService:
    def __init__(
        self, 
        file_handler: IFileWriter,
        tinh_cuoc_service: TinhCuocService,
        thong_ke_service: ThongKeService
    ):
        self.file_handler = file_handler
        self.tinh_cuoc_service = tinh_cuoc_service
        self.thong_ke_service = thong_ke_service

    def ghi_ket_qua(self, file_path: str, khach_hang_dict: Dict[str, KhachHang]) -> None:
        lines = []
        for so_dt, kh in khach_hang_dict.items():
            tong_tien = sum(
                self.tinh_cuoc_service.tinh_tien_cuoc_goi(cg) 
                for cg in kh.cuoc_goi
            )
            thong_ke = self.thong_ke_service.dem_cuoc_goi_theo_vung(kh.cuoc_goi)
            
            line = (
                f"{kh.ten}; {kh.so_dt}; {tong_tien:.0f}; "
                f"{thong_ke['NH']}; {thong_ke['LC']}; "
                f"{thong_ke['X']}; {thong_ke['RX']}\n"
            )
            lines.append(line)
        
        self.file_handler.write(file_path, lines)

class PhoneBillingApplication:
    def __init__(
        self,
        khach_hang_repo: KhachHangRepository,
        cuoc_goi_repo: CuocGoiRepository,
        bao_cao_service: BaoCaoService
    ):
        self.khach_hang_repo = khach_hang_repo
        self.cuoc_goi_repo = cuoc_goi_repo
        self.bao_cao_service = bao_cao_service

    def process(self, 
                khach_hang_file: str,
                cuoc_goi_file: str,
                ket_qua_file: str) -> None:
        khach_hang_dict = self.khach_hang_repo.load_khach_hang(khach_hang_file)
        self.cuoc_goi_repo.load_cuoc_goi(cuoc_goi_file, khach_hang_dict)
        self.bao_cao_service.ghi_ket_qua(ket_qua_file, khach_hang_dict)

def main():
    file_handler = TextFileHandler()
    khach_hang_repo = KhachHangRepository(file_handler)
    cuoc_goi_repo = CuocGoiRepository(file_handler)
    giam_gia_service = GiamGiaService()
    tinh_cuoc_service = TinhCuocService(giam_gia_service)
    thong_ke_service = ThongKeService()
    bao_cao_service = BaoCaoService(file_handler, tinh_cuoc_service, thong_ke_service)
    
    app = PhoneBillingApplication(khach_hang_repo, cuoc_goi_repo, bao_cao_service)
    app.process('khachhang.txt', 'cuocgoi.txt', 'ketqua.txt')

if __name__ == "__main__":
    main()