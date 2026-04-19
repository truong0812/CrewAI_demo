"""
Research Task - Nhiem vu nghien cuu chi tiet dua tren outline.
"""

from crewai import Task


def create_research_task(agent, topic: str, outline: str = None) -> Task:
    """Tao task nghien cuu chu de dua tren outline cu the."""
    
    if outline:
        # Research dua tren outline cu the
        return Task(
            description=f"""
            Ban can nghien cuu CHI TIET de ho tro viec viet tai lieu thuyet trinh ve: "{topic}"

            === OUTLINE BAI THUYET TRINH ===
            {outline}
            === HET OUTLINE ===

            Yeu cau nghien cuu:
            1. Phan tich tung slide trong outline va xac dinh thong tin can nghien cuu them
            2. Tim kiem thong tin CHI TIET cho moi muc trong outline:
               - So lieu, thong ke cu the voi NGUON
               - Vi du thuc te, case study
               - Dinh nghia chuyen giai chinh xac
               - Xu huong va du bao co nguon
            3. Moi thong tin quan trong PHAI CO NGUON:
               - Ten nguon (bao cao, to chuc, tac gia)
               - Nam xuat ban/phat hanh
               - URL neu co
            4. To chuc thong tin theo cau truc outline:
               - Moi phan tuong ung voi mot slide
               - Thong tin day du, chinh xac, co the tin cay duoc

            Chu de: {topic}

            Dinh dang ket qua:
            ```
            == Slide [X]: [Tieu de slide] ==
            - Thong tin 1 (Nguon: Ten nguon, Nam, URL)
            - Thong tin 2 (Nguon: Ten nguon, Nam, URL)
            - Vi du: [mo ta] (Nguon: Ten nguon, Nam)
            - So lieu: [du lieu] (Nguon: Ten nguon, Nam)
            
            == Slide [Y]: [Tieu de slide] ==
            ...
            ```

            QUAN TRONG:
            - Thong tin phai CHINH XAC va co NGUON ro rang
            - Uu tien so lieu va vi du cu the
            - Khong duoc bia dat thong tin
            - Trinh bay ket qua co cau truc ro rang bang tieng Viet
            """,
            agent=agent,
            expected_output="Bao cao nghien cuu chi tiet bang tieng Viet, to chuc theo outline, voi NGUON THAM KHAO ro rang cho moi thong tin quan trong. Moi phan tuong ung voi mot slide trong outline.",
        )
    else:
        # Research tong quat (fallback khi khong co outline)
        return Task(
            description=f"""
            Nghien cuu chu de sau mot cach toan dien va chi tiet: "{topic}"

            Yeu cau:
            1. Tim hieu cac khia canh chinh cua chu de
            2. Thu thap thong tin quan trong, so lieu, vi du thuc te voi NGUON
            3. Xac dinh cac diem then chot can dua vao bai thuyet trinh
            4. To chuc thong tin theo thu tu logic:
               - Gioi thieu / Tong quan
               - Cac noi dung chinh (3-7 phan)
               - Ket luan / Tom tat
            5. Moi phan can co thong tin chi tiet du de tao slide
            6. Moi thong tin quan trong phai co NGUON (ten nguon, nam, URL neu co)

            Chu de: {topic}

            Hay nghien cuu sau va trinh bay ket qua mot cach co cau truc ro rang bang tieng Viet.
            """,
            agent=agent,
            expected_output="Bao cao nghien cuu chi tiet bang tieng Viet, co cau truc ro rang voi cac phan: Gioi thieu, Noi dung chinh (3-7 phan), Ket luan. Moi phan co thong tin cu the, vi du, so lieu voi NGUON tham khao.",
        )