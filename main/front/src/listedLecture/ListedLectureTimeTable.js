import React, { useState } from "react";

const ListedLectureTimeTable = ({
  lectures,
  priority,
  updateLecturePriority,
  updateLectureInfo,
}) => {
  let maxDay = 0;
  let maxHour = 0;
  let hasZeroHour = false;

  const [editingLectureIndex, setEditingLectureIndex] = useState(null);
  const [memo, setMemo] = useState("");
  const [classroom, setClassroom] = useState("");

  lectures.forEach((lecture) => {
    if (lecture.lecTime && lecture.lecTime !== "0" && lecture.lectime == null) {
      const times = lecture.lecTime.split(",");
      times.forEach((time) => {
        const [day, hour] = time.replace(/[()]/g, "").split(":").map(Number);
        if (day > maxDay) maxDay = day;
        if (hour > maxHour) maxHour = hour;

        if (hour === 0) {
          hasZeroHour = true;
        }
      });
    }
  });

  const handleEditClick = (lecture, rowIndex, cellIndex, index) => {
    setEditingLectureIndex(`${rowIndex}-${cellIndex}-${index}`);
    setMemo(lecture.memo || "");
    setClassroom(lecture.classroom || "");
  };

  const handleUpdate = async (lecture) => {
    await updateLectureInfo({
      user_id: lecture.user_id,
      lecNumber: lecture.lecNumber,
      year: lecture.year,
      semester: lecture.semester,
      memo,
      classroom,
    });
    setEditingLectureIndex(null);
  };

  const timetable = Array.from(
    { length: hasZeroHour ? maxHour + 1 : maxHour },
    () =>
      Array(maxDay)
        .fill(null)
        .map(() => [])
  );
  const noTimeLectures = [];

  lectures.forEach((lecture) => {
    if (lecture.lecTime && lecture.lecTime !== "0" && lecture.lectime == null) {
      const times = lecture.lecTime.split(",");
      times.forEach((time) => {
        const [day, hour] = time.replace(/[()]/g, "").split(":").map(Number);
        if (hour >= 0 && hour < timetable.length) {
          timetable[hour][day - 1].push(lecture);
        }
      });
    } else {
      noTimeLectures.push(lecture);
    }
  });

  const daysOfWeek = ["월", "화", "수", "목", "금", "토", "일"];

  return (
    <div>
      <table>
        <thead>
          <tr>
            {daysOfWeek.slice(0, maxDay).map((day, index) => (
              <th key={index}>{day}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {hasZeroHour && (
            <tr>
              <td>0교시</td>
              {Array(maxDay)
                .fill(null)
                .map((_, cellIndex) => (
                  <td key={cellIndex}>
                    {timetable[0][cellIndex].length > 0 ? (
                      timetable[0][cellIndex].map((lecture, index) => (
                        <div key={index}>
                          <input
                            type="checkbox"
                            checked={
                              lecture.priority &&
                              lecture.priority.split(" ").includes(priority)
                            }
                            onChange={() =>
                              updateLecturePriority(lecture.lecNumber, priority)
                            }
                          />
                          <p>{lecture.lecName}</p>
                          <p>{lecture.lecProfessor}</p>
                          {editingLectureIndex ===
                            `0-${cellIndex}-${index}` && (
                            <div>
                              <input
                                type="text"
                                value={memo}
                                onChange={(e) => setMemo(e.target.value)}
                                placeholder="메모"
                              />
                              <input
                                type="text"
                                value={classroom}
                                onChange={(e) => setClassroom(e.target.value)}
                                placeholder="강의실"
                              />
                              <button onClick={() => handleUpdate(lecture)}>
                                완료
                              </button>
                            </div>
                          )}
                          <button
                            onClick={() =>
                              handleEditClick(lecture, 0, cellIndex, index)
                            }
                          >
                            수정
                          </button>
                        </div>
                      ))
                    ) : (
                      <div></div>
                    )}
                  </td>
                ))}
            </tr>
          )}
          {timetable.slice(hasZeroHour ? 1 : 0).map((row, rowIndex) => (
            <tr key={rowIndex + (hasZeroHour ? 1 : 0)}>
              <td>{rowIndex + (hasZeroHour ? 1 : 0)}교시</td>
              {row.map((cell, cellIndex) => (
                <td key={cellIndex}>
                  {cell.length > 0 ? (
                    cell.map((lecture, index) => (
                      <div key={index}>
                        <input
                          type="checkbox"
                          checked={
                            lecture.priority &&
                            lecture.priority.split(" ").includes(priority)
                          }
                          onChange={() =>
                            updateLecturePriority(lecture.lecNumber, priority)
                          }
                        />
                        <p>{lecture.lecName}</p>
                        <p>{lecture.lecProfessor}</p>
                        {editingLectureIndex ===
                          `${
                            rowIndex + (hasZeroHour ? 1 : 0)
                          }-${cellIndex}-${index}` && ( // 수정된 부분
                          <div>
                            <input
                              type="text"
                              value={memo}
                              onChange={(e) => setMemo(e.target.value)}
                              placeholder="메모"
                            />
                            <input
                              type="text"
                              value={classroom}
                              onChange={(e) => setClassroom(e.target.value)}
                              placeholder="강의실"
                            />
                            <button onClick={() => handleUpdate(lecture)}>
                              완료
                            </button>
                          </div>
                        )}
                        <button
                          onClick={() =>
                            handleEditClick(
                              lecture,
                              rowIndex + (hasZeroHour ? 1 : 0),
                              cellIndex,
                              index
                            )
                          }
                        >
                          {" "}
                          {/* 수정된 부분 */}
                          수정
                        </button>
                      </div>
                    ))
                  ) : (
                    <div></div>
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {noTimeLectures.length > 0 && (
        <div>
          {noTimeLectures.map((lecture, index) => (
            <p key={index}>
              {lecture.lecName} | {lecture.lecProfessor}
            </p>
          ))}
        </div>
      )}
    </div>
  );
};

export default ListedLectureTimeTable;
