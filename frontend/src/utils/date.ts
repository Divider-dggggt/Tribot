export const formatCaseDateTime = (date = new Date()): string => {
  date.setHours(date.getHours() + 10); // TODO: remove once BE is fixed
  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const year = date.getFullYear();
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");

  return `${day}/${month}/${year} ${hours}:${minutes}`;
};

export const parseCaseDateTime = (dateText: string): number => {
  const customFormatMatch = dateText.match(
    /^(\d{2})\/(\d{2})\/(\d{4})\s+(\d{2}):(\d{2})(?::(\d{2}))?$/
  );

  if (customFormatMatch) {
    const [, day, month, year, hours, minutes, seconds] = customFormatMatch;
    const parsedDate = new Date(
      Number(year),
      Number(month) - 1,
      Number(day),
      Number(hours),
      Number(minutes),
      Number(seconds ?? "0")
    );
    return parsedDate.getTime();
  }

  return new Date(dateText).getTime();
};
