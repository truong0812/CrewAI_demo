"""
Content Tasks - Nhiem vu tao outline va chinh sua outline tu gop y.
"""

from crewai import Task


def create_content_task(agent, topic: str, num_slides: int = 10, user_outline_hint: str = "") -> Task:
    """Tao task thiet ke outline slide o buoc dau tien cua workflow."""
    return Task(
        description=f"""
        Hay tao outline chi tiet cho bai thuyet trinh ve: "{topic}".

        Workflow cua he thong la:
        1. Tao outline truoc
        2. Sau khi outline duoc duyet moi bat dau research
        3. Research se duoc dung de viet speaker doc chi tiet

        Goi y outline/co cau truc nguoi dung da cung cap neu co:
        {user_outline_hint or "Khong co. Hay de xuat cau truc hop ly tu chu de."}

        Yeu cau ve outline:
        1. So luong slide muc tieu: {num_slides} slide (co the linh hoat +/-2 neu thuc su can thiet)
        2. Slide dau tien phai la slide tieu de (type: "title")
        3. Slide cuoi cung phai la slide tom tat/cam on (type: "summary")
        4. Cac slide o giua la slide noi dung (type: "content")
        5. Moi slide noi dung chi nen co 3-6 bullet points cot loi
        6. Tieu de slide phai ngan gon, ro y va phu hop cho thuyet trinh
        7. Moi bullet point chi nen la y chinh de lam co so cho buoc research sau do
        8. Notes tren outline chi la huong dan ngan cho huong phat trien noi dung, khong can viet thanh tai lieu day du
        9. Cau truc phai du de sau nay co the research tung slide va viet speaker doc chi tiet, co nguon ro rang

        QUAN TRONG - Xuat ket qua theo DUNG JSON format sau:
        ```json
        {{
            "presentation_title": "Tieu de bai thuyet trinh",
            "slides": [
                {{
                    "type": "title",
                    "title": "Tieu de chinh",
                    "subtitle": "Phu de hoac mo ta ngan",
                    "notes": "Huong dan ngan cho huong mo dau"
                }},
                {{
                    "type": "content",
                    "title": "Tieu de slide noi dung",
                    "bullet_points": [
                        "Diem chinh 1",
                        "Diem chinh 2",
                        "Diem chinh 3"
                    ],
                    "notes": "Goi y research va huong trien khai cho slide nay"
                }},
                {{
                    "type": "summary",
                    "title": "Tom tat & Cam on",
                    "bullet_points": [
                        "Tom tat diem 1",
                        "Tom tat diem 2"
                    ]
                }}
            ]
        }}
        ```

        Toan bo noi dung phai bang tieng Viet. Chi xuat JSON, khong them giai thich.
        """,
        agent=agent,
        expected_output='JSON string theo dung format yeu cau, chua presentation_title va danh sach slides. Moi slide co type, title, bullet_points (voi content/summary), notes. Toan bo bang tieng Viet.',
    )


def create_revise_content_task(agent, current_outline: str, feedback: str, topic: str) -> Task:
    """Tao task chinh sua outline dua tren gop y cua nguoi dung."""
    return Task(
        description=f"""
        Ban can chinh sua outline bai thuyet trinh ve "{topic}" dua tren gop y cua nguoi dung.

        === OUTLINE HIEN TAI ===
        {current_outline}
        === HET OUTLINE HIEN TAI ===

        === GOP Y CUA NGUOI DUNG ===
        {feedback}
        === HET GOP Y ===

        Yeu cau:
        1. Giu nguyen JSON format nhu outline hien tai
        2. Ap dung cac thay doi theo gop y cua nguoi dung
        3. Dam bao van tuan thu workflow: outline phai la khung cho buoc research va viet speaker doc sau do
        4. Moi slide nen co 3-6 bullet points cot loi, ngan gon, de lam dau vao cho research
        5. Giu nguyen slide tieu de (type: "title") va slide cuoi (type: "summary") neu khong can sua
        6. Dam bao luong thong tin van logic sau khi chinh sua

        QUAN TRONG - Xuat ket qua theo DUNG JSON format:
        ```json
        {{
            "presentation_title": "Tieu de bai thuyet trinh",
            "slides": [
                {{
                    "type": "title",
                    "title": "Tieu de chinh",
                    "subtitle": "Phu de",
                    "notes": "Huong dan ngan"
                }},
                {{
                    "type": "content",
                    "title": "Tieu de slide",
                    "bullet_points": ["Diem 1", "Diem 2"],
                    "notes": "Goi y research/speaker notes"
                }},
                {{
                    "type": "summary",
                    "title": "Tom tat & Cam on",
                    "bullet_points": ["Tom tat 1"]
                }}
            ]
        }}
        ```

        Toan bo noi dung phai bang tieng Viet. Chi xuat JSON, khong them giai thich.
        """,
        agent=agent,
        expected_output='JSON string da chinh sua theo dung format yeu cau, ap dung cac gop y cua nguoi dung. Toan bo bang tieng Viet.',
    )
