from pdfminer.converter import XMLConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from io import StringIO, BytesIO
from typing import Container

def convert_pdf_to_xml(
    pdf_path: str,
    format: str = "text",
    codec: str = "utf-8",
    password: str = "",
    maxpages: int = 0,
    caching: bool = True,
    pagenos: Container[int] = set(),
) -> str:
    """Summary
    Parameters
    ----------
    path : str
        Path to the pdf file
    format : str, optional
        Format of output, must be one of: "text", "html", "xml".
        By default, "text" format is used
    codec : str, optional
        Encoding. By default "utf-8" is used
    password : str, optional
        Password
    maxpages : int, optional
        Max number of pages to convert. By default is 0, i.e. reads all pages.
    caching : bool, optional
        Caching. By default is True
    pagenos : Container[int], optional
        Provide a list with numbers of pages to convert
    Returns
    -------
    str
        Converted pdf file
    """
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    laparams = LAParams()
    device = XMLConverter(rsrcmgr, retstr, laparams=laparams)

    fp = open(pdf_path, "rb")
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    for page in PDFPage.get_pages(
        fp,
        pagenos,
        maxpages=maxpages,
        password=password,
        caching=caching,
        check_extractable=True,
    ):
        interpreter.process_page(page)
    text = retstr.getvalue()#.decode()
    if not text.endswith('</pages>') or not text.endswith('</pages>\n'): text += '\n</pages>'
    fp.close()
    device.close()
    retstr.close()

    xml_filepath = pdf_path.replace('.pdf', '.xml')

    with open(xml_filepath, 'w') as f:
        f.write(text)
    f.close()



    return xml_filepath

# 'C:\\Users\\ga78jem\\Documents\\20220309.pdf'
#pdf_filepath = "C:/Users/ga78jem/Documents/Revit/Exports/floorplan_zPos_0.42_roomWidth_0.24_numRleft_2.0_numRright_2.0.txt.pdf.pdf"
#"C:\\Users\\ga78jem\\Documents\\Revit\\Exports\\floorplan_zPos_0.42_roomWidth_0.24_numRleft_2.0_numRright_2.0\\floorplan_zPos_0.42_roomWidth_0.24_numRleft_2.0_numRright_2.0.pdf.pdf"
#xml_text = convert_pdf_to_xml(pdf_filepath, 1)
