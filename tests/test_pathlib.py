import pathlib


def test_convert_path():
    
    src = "C:/Users/debru/Documents/xyz_workspace/Attachments/Document request/Diego_heure_gaulois.docx"
    s_dir = "C:/Users/debru/Documents/xyz_workspace/Attachments/Document request"
    p = pathlib.Path(src)
    print(f"raw: {p}")
    print(f"posix: {p.as_posix()}")
    win_p = pathlib.PureWindowsPath(src)
    win_d = pathlib.PureWindowsPath(s_dir)
    print(f"PureWindowsPath: {str(win_p)}")
    win_pdf = win_d.joinpath("test.pdf")
    print(f"PureWindowsPath: {str(win_pdf)}")
    print(pathlib.PureWindowsPath(f"{s_dir}/test.pdf"))

