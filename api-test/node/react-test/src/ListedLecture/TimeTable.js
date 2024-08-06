import React from "react";

const Timetable = ({ checkedLectures }) => {
  const renderTimetable = () => {
    let timetable = Array(5)
      .fill(null)
      .map(() => Array(7).fill(null));

    checkedLectures.forEach((lecture) => {
      const times = lecture.lecTime.match(/\((\d+):(\d+)\)/g);
      if (times) {
        times.forEach((time) => {
          const [_, col, row] = time.match(/\((\d+):(\d+)\)/);

          while (timetable.length < row) {
            timetable.push(Array(timetable[0].length).fill(null));
          }
          while (timetable[0].length < col) {
            timetable = timetable.map((row) => [...row, null]);
          }

          timetable[row - 1][
            col - 1
          ] = `${lecture.lecClassName} (${lecture.lecProfessor})`;
        });
      }
    });

    return timetable.map((row, rowIndex) => (
      <tr key={rowIndex}>
        {row.map((cell, colIndex) => (
          <td key={colIndex}>{cell}</td>
        ))}
      </tr>
    ));
  };

  const renderNullLectures = () => {
    return checkedLectures
      .filter((lecture) => !lecture.lecTime.match(/\((\d+):(\d+)\)/g))
      .map((lecture, index) => (
        <p key={index}>
          {lecture.lecClassName} ({lecture.lecProfessor})
        </p>
      ));
  };

  return (
    <div>
      <table border="1">
        <tbody>{renderTimetable()}</tbody>
      </table>
      {renderNullLectures()}
    </div>
  );
};

export default Timetable;
