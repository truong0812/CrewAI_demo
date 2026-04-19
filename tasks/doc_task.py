"""
Writer Tasks - Nhiem vu viet speaker doc chi tiet cho nguoi thuyet trinh.
"""

from crewai import Task


def create_doc_task(agent, approved_outline: str, research_result: str, topic: str) -> Task:
    """Tao task viet speaker doc chi tiet (Markdown) cho nguoi thuyet trinh."""
    return Task(
        description=f"""
        Dua tren outline da duyet va ket qua research, hay viet mot SPEAKER DOC CHI TIET bang Markdown
        danh cho NGUOI THUYET TRINH ve chu de "{topic}".

        === OUTLINE DA DUYET ===
        {approved_outline}
        === HET OUTLINE ===

        === KET QUA RESEARCH ===
        {research_result}
        === HET KET QUA RESEARCH ===

        Muc tieu tai lieu:
        - Giup nguoi thuyet trinh hieu tung slide, noi tu tin va co dan chung ro rang
        - Khong viet lai slide theo kieu ngan gon; day la tai lieu hau truong, chi tiet
        - Moi slide trong outline phai tro thanh mot muc rieng trong tai lieu

        YEU CAU BAT BUOC:
        1. Moi slide trong outline tuong ung voi mot section Markdown dang:
           ## Slide X: [Tieu de]
        2. Moi section phai co day du cac phan sau:
           - **Muc tieu slide**
           - **Noi dung thuyet trinh chi tiet**
           - **Du lieu/vi du/case study nen dung**
           - **Bullet points dua len slide**
           - **Speaker notes**
           - **Nguon tham khao**
        3. Speaker doc phai chi tiet den muc nguoi thuyet trinh co the dung no de noi 3-7 phut cho moi slide noi dung
        4. Moi so lieu, thong ke, nhan dinh quan trong, trich dan, du bao deu phai co nguon ro rang
        5. Neu research khong co can cu cho mot thong tin, khong duoc bo sung nhu mot su that
        6. Phan "Bullet points dua len slide" phai ngan gon, phu hop de bien thanh slide
        7. Phan "Nguon tham khao" phai liet ke ro tung nguon da dung trong section do

        QUY CACH NGUON THAM KHAO:
        - Trong noi dung, gan nguon ngay sau thong tin quan trong
        - Dung dinh dang: (Nguon: Ten nguon, Nam, URL)
        - Cuoi section, tong hop lai duoi dang danh sach:
          - [1] Ten nguon, Nam. Tieu de/bao cao. URL
          - [2] ...
        - Uu tien nguon uy tin: co quan nha nuoc, to chuc quoc te, bao cao doanh nghiep/consulting uy tin, paper, dataset, website chinh thuc

        Dinh dang markdown mau:
        ```markdown
        # [Tieu de bai thuyet trinh]

        ## Slide 1: [Tieu de slide]
        **Loai:** title

        **Muc tieu slide:**
        [Slide nay dung de lam gi trong mach bai]

        **Noi dung thuyet trinh chi tiet:**
        [Phan dien giai chi tiet, co nguon trong dong khi can]

        **Du lieu/vi du/case study nen dung:**
        - [Vi du 1] (Nguon: ...)
        - [Vi du 2] (Nguon: ...)

        **Bullet points dua len slide:**
        - Diem 1
        - Diem 2

        **Speaker notes:**
        [Huong dan mo dau, chuyen y, nhan manh, cau hoi goi mo]

        **Nguon tham khao:**
        - [1] ...
        - [2] ...

        ---
        ```

        QUAN TRONG:
        - Toan bo bang tieng Viet
        - Viet ro rang, co chieu sau, khong viet chung chung
        - Khong bo sot slide nao trong outline
        - Khong duoc xuat JSON, chi xuat Markdown
        """,
        agent=agent,
        expected_output="Tai lieu Markdown chi tiet bang tieng Viet danh cho nguoi thuyet trinh, co section theo tung slide, speaker notes huu ich va nguon tham khao ro rang cho moi thong tin quan trong.",
    )


def create_revise_doc_task(agent, current_doc: str, feedback: str, topic: str) -> Task:
    """Tao task chinh sua speaker doc dua tren gop y/review."""
    return Task(
        description=f"""
        Ban can chinh sua speaker doc ve "{topic}" dua tren feedback duoi day.

        === SPEAKER DOC HIEN TAI ===
        {current_doc}
        === HET SPEAKER DOC ===

        === FEEDBACK ===
        {feedback}
        === HET FEEDBACK ===

        Yeu cau:
        1. Giu nguyen cau truc Markdown tong the cua tai lieu
        2. Ap dung day du cac thay doi theo feedback
        3. Dam bao moi thong tin quan trong van co nguon ro rang
        4. Neu them noi dung moi, phai bo sung nguon tuong ung
        5. Giu tai lieu o vai tro speaker doc: chi tiet, huu ich, co tinh trinh bay thuc chien
        6. Khong xoa di phan "Nguon tham khao" cua tung section
        7. Chi xuat Markdown da chinh sua, khong them giai thich
        """,
        agent=agent,
        expected_output="Speaker doc Markdown da chinh sua theo feedback, giu nguyen tinh chat chi tiet cho nguoi thuyet trinh va nguon tham khao ro rang.",
    )
