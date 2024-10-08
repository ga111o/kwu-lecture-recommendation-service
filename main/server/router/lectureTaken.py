import math
from typing import List, Dict, Optional, Union
from fastapi import FastAPI, HTTPException, Request, Depends, HTTPException, Cookie, APIRouter
from pydantic import BaseModel
import sqlite3
import uvicorn
import os
from fastapi.security import OAuth2AuthorizationCodeBearer
from fastapi.responses import RedirectResponse
import httpx
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from datetime import timedelta
from db import db_connect
from model import OCRResponse, OCRRequest, OCRLectureInfo, TakenLectureManaullyUpdate, TakenLectureDelete, userID, TakenLectureUpdate, TakenLectureAutoUpdate

router = APIRouter()


def updateUserGPA(userID):
    conn = db_connect()
    cursor = conn.cursor()

    grade_points = {
        'A+': 4.5,
        'A': 4.0,
        'B+': 3.5,
        'B': 3.0,
        'C+': 2.5,
        'C': 2.0,
        'P': 0.0,
        'NP': 0.0,
        'F': 0.0
    }

    cursor.execute("""
    SELECT userCredit
    FROM UserTakenLecture
    WHERE user_id = ?
    """, (userID,))

    user_credits = cursor.fetchall()
    total_score = 0
    total_courses = 0

    for row in user_credits:
        credit = row[0]
        if credit in grade_points:
            total_score += grade_points[credit]
            total_courses += 1

    total_gpa = total_score / total_courses if total_courses > 0 else 0.0
    total_gpa = math.floor(total_gpa * 100) / 100

    cursor.execute("""
    SELECT userCredit
    FROM UserTakenLecture
    WHERE user_id = ? AND Classification IN ('전선', '전필')
    """, (userID,))

    major_credits = cursor.fetchall()
    major_score = 0
    major_courses = 0

    for row in major_credits:
        credit = row[0]
        if credit in grade_points:
            major_score += grade_points[credit]
            major_courses += 1

    major_gpa = major_score / major_courses if major_courses > 0 else 0.0
    major_gpa = math.floor(major_gpa * 100) / 100

    cursor.execute("""
    UPDATE User
    SET totalGPA = ?, majorGPA = ?
    WHERE user_id = ?
    """, (total_gpa, major_gpa, userID))

    conn.commit()
    conn.close()


@router.post("/ocr", response_model=OCRResponse)
async def update_lecture_data_by_ocr(request: OCRRequest):
    conn = db_connect()
    cursor = conn.cursor()
    user_taken_lectures = set()
    splited_ocr_data = []

    try:
        for ocr_text in request.ocrResults:
            words = ocr_text.split()
            filtered_words = [word for word in words if len(word) >= 3]
            splited_ocr_data.extend(filtered_words)

        for word in splited_ocr_data:
            cursor.execute(
                "SELECT lecName, lecClassification, lecCredit FROM LectureList WHERE lecName LIKE ?", ('%' + word + '%',))
            rows = cursor.fetchall()
            for row in rows:
                lecture_info = OCRLectureInfo(
                    lectureName=row[0],
                    lecClassification=row[1],
                    lecCredit=row[2]
                )
                user_taken_lectures.add(lecture_info)

                cursor.execute(
                    "SELECT COUNT(*) FROM UserTakenLecture WHERE lecName = ? AND Classification = ? AND lecCredit = ? AND user_id = ?",
                    (row[0], row[1], row[2], request.user_id)
                )
                count = cursor.fetchone()[0]

                if count == 0:
                    insert_query = """
                        INSERT INTO UserTakenLecture (lecName, Classification, lecCredit, user_id)
                        VALUES (?, ?, ?, ?)
                    """
                    cursor.execute(insert_query, (
                        row[0],
                        row[1],
                        row[2],
                        request.user_id
                    ))

        conn.commit()
        print("done?")

    except Exception as e:
        conn.rollback()
        print("Error occurred:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()

    return OCRResponse(userTakenLectures=list(user_taken_lectures))


@router.post("/user/add_taken_lecture_manually")
async def add_user_taken_lecture_manually(input_data: TakenLectureManaullyUpdate):
    conn = db_connect()
    cursor = conn.cursor()

    insert_query = """
        INSERT INTO UserTakenLecture (lecName, Classification, lecCredit, userCredit, user_id)
        VALUES (?, ?, ?, ?, ?)
    """

    try:
        cursor.execute(insert_query, (
            input_data.lecName,
            input_data.Classification,
            input_data.lecCredit,
            input_data.userCredit,
            input_data.user_id
        ))

        conn.commit()

        updateUserGPA(input_data.user_id)

        return {"message": "successfully added taken lecture"}

    except Exception as e:
        conn.rollback()
        print("Error occurred:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()


@router.post("/user/delete_taken_lecture")
async def delete_user_taken_lecture(input_data: TakenLectureDelete):
    conn = db_connect()
    cursor = conn.cursor()

    update_query = """
        delete from UserTakenLecture
        where id = ?  
        and user_id = ? 
    """

    try:
        cursor.execute(update_query, (
            input_data.id,
            input_data.user_id
        ))

        conn.commit()

        updateUserGPA(input_data.user_id)

        return {"message": "delete taken lecture"}

    except Exception as e:
        conn.rollback()
        print("Error occurred:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()


@router.post("/user/get_taken_lectures")
async def get_user_taken_lectures(request: userID):
    conn = db_connect()
    cursor = conn.cursor()

    select_query = """
        SELECT id, lecName, Classification, lecCredit, userCredit, year, semester, lecNumber
        FROM UserTakenLecture
        WHERE user_id = ?
    """

    try:
        cursor.execute(select_query, (request.user_id,))
        lectures = cursor.fetchall()

        lectures_list = []
        for lecture in lectures:
            lectures_list.append({
                "id": lecture[0],
                "lecName": lecture[1],
                "Classification": lecture[2],
                "lecCredit": lecture[3],
                "userCredit": lecture[4],
                "year": lecture[5],
                "semester": lecture[6],
                "lecNumber": lecture[7],
            })

        return {"taken_lectures": lectures_list}

    except Exception as e:
        print("Error occurred:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()


@router.post("/user/update_taken_lecture")
async def update_user_taken_lecture(input_data: TakenLectureUpdate):
    conn = db_connect()
    cursor = conn.cursor()

    print(input_data.userCredit)

    update_query = """
        UPDATE UserTakenLecture
        SET Classification = ?, lecCredit = ?, userCredit = ?, lecName = ?
        WHERE id = ?  AND user_id = ?
    """

    try:
        cursor.execute(update_query, (
            input_data.Classification,
            input_data.lecCredit,
            input_data.userCredit,
            input_data.lecName,
            input_data.id,
            input_data.user_id,
        ))

        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Lecture not found")

        updateUserGPA(input_data.user_id)

        return {"message": "updated taken lecture info"}

    except Exception as e:
        conn.rollback()
        print("Error occurred:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()


@router.post("/user/add_taken_lecture_auto")
async def add_taken_lecture_auto(input_data: TakenLectureAutoUpdate):
    conn = db_connect()
    cursor = conn.cursor()

    try:
        check_query = """
        SELECT COUNT(*) 
        FROM UserTakenLecture 
        WHERE user_id = ? AND lecNumber = ? AND year = ? AND semester = ?
        """
        cursor.execute(check_query, (input_data.user_id,
                                     input_data.lecNumber, input_data.year, input_data.semester))
        count = cursor.fetchone()[0]

        if count > 0:
            raise HTTPException(
                status_code=400, detail="Lecture already taken")

        if input_data.lecNumber.startswith("user"):
            insert_query = """
            INSERT INTO UserTakenLecture (user_id, lecName, Classification, year, semester, lecNumber, lecCredit) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(insert_query, (input_data.user_id, input_data.lecName, "기타",
                                          input_data.year, input_data.semester, input_data.lecNumber, 0))

            update_query = """
            UPDATE UserListedLecture 
            SET isCompleted = ? 
            WHERE user_id = ? AND lecNumber = ? AND year = ? AND semester = ?
            """
            cursor.execute(update_query, (True, input_data.user_id,
                                          input_data.lecNumber, input_data.year, input_data.semester))

        else:
            query = """
            SELECT lecCredit, lecClassification, lecTheme, lectureID 
            FROM LectureList 
            WHERE lecNumber = ? AND year = ? AND semester = ? AND lecName = ?
            """
            cursor.execute(query, (input_data.lecNumber, input_data.year,
                                   input_data.semester, input_data.lecName))
            lecture_info = cursor.fetchone()

            if lecture_info is None:
                raise HTTPException(
                    status_code=404, detail="Lecture not found")

            lecCredit, lecClassification, lecTheme, lectureID = lecture_info

            major_query = """
            SELECT majorRecogBunBan 
            FROM LectureConditions 
            WHERE lectureID = ?
            """
            cursor.execute(major_query, (lectureID,))
            major_info = cursor.fetchone()

            majorRecogBunBan = major_info[0] if major_info else None

            insert_query = """
            INSERT INTO UserTakenLecture (user_id, lecName, Classification, lecCredit, year, semester, lecNumber, lecTheme, majorRecogBunBan) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(insert_query, (input_data.user_id, input_data.lecName, lecClassification,
                                          lecCredit, input_data.year, input_data.semester, input_data.lecNumber, lecTheme, majorRecogBunBan))

            update_query = """
            UPDATE UserListedLecture 
            SET isCompleted = ? 
            WHERE user_id = ? AND lecNumber = ? AND year = ? AND semester = ?
            """
            cursor.execute(update_query, (True, input_data.user_id,
                                          input_data.lecNumber, input_data.year, input_data.semester))

        conn.commit()

        return {"message": "lecture completed done"}

    except Exception as e:
        conn.rollback()
        print("Error occurred:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()
