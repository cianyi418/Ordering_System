import logging


# Append a row to the Google Sheets by header
def append_by_header(sheet, row_data: dict, header_row_index=1):
    """
    根據欄位名稱 (header) 的順序，把 dict 資料寫入 Google Sheet 的下一列。
    缺漏的欄位會自動填空字串，多餘的欄位會被忽略。
    
    :param sheet: gspread 工作表物件
    :param row_data: 欲寫入的 dict 資料，key 為欄位名稱
    :param header_row_index: 表頭所在的列（預設是第 1 列）
    """
    headers = sheet.row_values(header_row_index)
    row = [row_data.get(header, '') for header in headers]
    sheet.append_row(row)

