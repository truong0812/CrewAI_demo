"""
Review Tasks - Nhiem vu kiem tra chat luong outline, speaker doc va slide.
"""

from crewai import Task


def create_outline_review_task(agent, outline_json: str, topic: str) -> Task:
    """Tao task kiem tra chat luong outline bai thuyet trinh."""
    return Task(
        description=f"""
        Hay kiem tra va danh gia chat luong cua outline bai thuyet trinh sau.

        Chu de yeu cau: {topic}

        === OUTLINE ===
        {outline_json}
        === HET OUTLINE ===

        Tieu chi danh gia:
        1. Do phu: outline co bao quat du chu de "{topic}" khong?
        2. Cau truc: co luong logic mo bai -> than bai -> ket bai khong?
        3. Kha nang research: tung slide co du ro de research sau do khong?
        4. Tieu de slide: ngan gon, ro y, phan anh dung noi dung khong?
        5. Bullet points: la y cot loi, khong qua chi tiet, khong trung lap khong?
        6. Tinh nhat quan: format va muc do chi tiet co dong deu khong?
        7. Tinh kha thi: co the dung outline nay de viet speaker doc chat luong cao khong?

        QUAN TRONG:
        - Chi danh gia "CAN SUA" neu co van de nghiem trong
        - Neu outline co the dung duoc va chi can tinh chinh nho -> "DAT"

        Dinh dang ket qua bat buoc:
        - Danh gia tong the: [1-2 cau]
        - Diem tot: [liet ke]
        - Van de (neu co): [liet ke cu the]
        - De xuat cai thien: [liet ke]
        - KET LUAN: DAT hoac CAN SUA
        """,
        agent=agent,
        expected_output="Bao cao danh gia chat luong outline bang tieng Viet. KET LUAN phai la 'DAT' hoac 'CAN SUA'.",
    )


def create_doc_review_task(agent, doc_content: str, topic: str) -> Task:
    """Tao task kiem tra chat luong speaker doc."""
    return Task(
        description=f"""
        Hay kiem tra va danh gia chat luong cua speaker doc sau.

        Chu de: {topic}

        === SPEAKER DOC ===
        {doc_content}
        === HET SPEAKER DOC ===

        Tieu chi danh gia:
        1. Noi dung: chinh xac, day du, co chieu sau va bam sat outline khong?
        2. Cau truc: moi slide co section ro rang va de theo doi khong?
        3. Tinh huu ich cho nguoi thuyet trinh: co giup noi thuc te, tu tin va co logic khong?
        4. Nguon trich dan: moi so lieu/claim quan trong co nguon ro rang va nhat quan khong?
        5. Vi du/case study: co du minh chung, cu the, khong chung chung khong?
        6. Bullet points va speaker notes: co tach biet ro, dung vai tro, phu hop de tao slide khong?
        7. Ngon ngu: tieng Viet ro rang, de hieu, de noi khong?

        QUAN TRONG:
        - Chi danh gia "CAN SUA" neu co van de nghiem trong
        - Thieu nguon cho cac claim quan trong duoc xem la van de nghiem trong
        - Neu tai lieu da dung duoc va chi can tinh chinh nho -> "DAT"

        Dinh dang ket qua bat buoc:
        - Danh gia tong the: [1-2 cau]
        - Diem tot: [liet ke]
        - Van de (neu co): [liet ke cu the]
        - De xuat cai thien: [liet ke]
        - KET LUAN: DAT hoac CAN SUA
        """,
        agent=agent,
        expected_output="Bao cao danh gia chat luong speaker doc bang tieng Viet. KET LUAN phai la 'DAT' hoac 'CAN SUA'.",
    )


def create_review_task(agent, slide_json: str) -> Task:
    """Tao task kiem tra chat luong slide JSON."""
    return Task(
        description=f"""
        Hay kiem tra va danh gia chat luong cua bai thuyet trinh sau.

        === SLIDE JSON ===
        {slide_json}
        === HET NOI DUNG ===

        Tieu chi danh gia:
        1. Noi dung: thong tin co chinh xac, day du va phu hop khong?
        2. Cau truc: luong thong tin co logic khong?
        3. Do dai: so luong slide va bullet points co phu hop khong?
        4. Tieu de: ngan gon, thu hut va phan anh dung noi dung khong?
        5. Bullet points: co suc tich, de doc va khong qua dai khong?
        6. Tinh nhat quan: format va phong cach co dong deu giua cac slide khong?
        7. Ngon ngu: tieng Viet co dung ngu phap va chinh ta khong?

        QUAN TRONG:
        - Chi danh gia "CAN SUA" neu co van de nghiem trong
        - Neu slide co the dung duoc va chi can tinh chinh nho -> "DAT"

        Dinh dang ket qua bat buoc:
        - Danh gia tong the: [1-2 cau]
        - Diem tot: [liet ke]
        - Van de (neu co): [liet ke cu the]
        - De xuat cai thien: [liet ke]
        - KET LUAN: DAT hoac CAN SUA
        """,
        agent=agent,
        expected_output="Bao cao danh gia chat luong slide bang tieng Viet. KET LUAN phai la 'DAT' hoac 'CAN SUA'.",
    )
