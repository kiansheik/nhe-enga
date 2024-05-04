import sys
from PyPDF2 import PdfReader, PdfWriter

def add_bookmarks(pdf_path, bookmarks, output_path):
    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    # Add all pages to the writer
    for page in reader.pages:
        writer.add_page(page)
    
    # Add bookmarks (now called outline items in PyPDF2 3.0.0+)
    for title, page in bookmarks.items():
        writer.add_outline_item(title, page - 1, parent=None)  # Subtract 1 because PyPDF2 is zero-indexed
    writer.page_mode = "/UseOutlines"
    # Write the new PDF with bookmarks
    with open(output_path, 'wb') as f:
        writer.write(f)

def main():
    pdf_path = sys.argv[1]
    output_path = 'bookmarked_kuapa.pdf'
    bookmarks = {
        "SUMÁRIO": 8,
        "APRESENTAÇÃO DO AUTOR": 10,
        "ALFABETO TUPI POTIGUARA": 15,
        "CAPÍTULO 1 - POTĨGUARA NHE'ENGA": 16,
        "MAS O QUE É GRAMÁTICA?": 20,
        "CAPÍTULO 2 – MOREYNHANGÁPE": 22,
        "SUBSTANTIVO": 24,
        "MARCADORES NÚMERO-PESSOAIS": 25,
        "DEMONSTRATIVO": 27,
        "CAPÍTULO 3 - PARAÍBA PORYPY": 28,
        "ESPECIFICAÇÕES DO SUBSTANTIVO": 29,
        "PARTÍCULAS DE LINGUAGEM AFETIVA": 31,
        "VOCATIVO": 32,
        "CAPÍTULO 4 - TORÉ RORYPABA": 35,
        "CONJUGAÇÕES VERBAIS": 38,
        "FORMA NEGATIVA DO VERBO": 39,
        "FORMA NOMINAL": 39,
        "MODO PERMISSIVO": 40,
        "MODO IMPERATIVO": 40,
        "CAPÍTULO 5 - POTĨGUARA RETAMA": 43,
        "NEOLOGISMOS": 46,
        "OS NUMERAIS": 47,
        "RELAÇÕES DE POSSE": 48,
        "PALAVRAS PLURIFORMES": 49,
        "CAPÍTULO 6 NHEMOSARAIETÁ": 53,
        "ESPECIFICADORES CIRCUNSTANCIAIS": 57,
        "TEMPO/ASPECTO VIA REDUPLICAÇÃO": 58,
        "POSPOSIÇÕES": 58,
        "CONJUNÇÕES": 60,
        "CAPÍTULO 7 - MOROMBO'ESABA ANAMA": 61,
        "SINTAXE": 68,
        "COMPLEMENTOS INDIRETOS": 68,
        "COMPLEMENTOS DIRETOS": 68,
        "CAPÍTULO 8 - TUIBA'E GUAIBĨ ABÉ": 73,
        "VARIAÇÕES LINGUÍSTICAS": 77,
        "VARIAÇÕES FONÉTICAS": 77,
        "AFIXOS CAUSATIVOS": 77,
        "CAPÍTULO 9 - ATUASABA 'YBOTYMIRĨ": 81,
        "MODO GERÚNDIO": 86,
        "CAPÍTULO 10 - NHEMOSARAIA ABAETÉ": 89,
        "MODO INDICATIVO CIRCUNSTANCIAL": 94,
        "DEVERBAIS": 95,
        "VERBOS IRREGULARES": 98,
        "CITAÇÕES DIRETAS": 100,
        "TEXTOS COMPLEMENTARES": 102,
        "GUIA DE EXPRESSÕES COTIDIANAS": 109,
        "VOCABULÁRIO TEMÁTICO": 114,
        "VERBOS E ADJETIVOS": 129,
        "VOCABULÁRIO EM ORDEM ALFABÉTICA": 135,
        "REFÊNCIAS BIBLIOGRÁFICAS": 156
    }

    add_bookmarks(pdf_path, bookmarks, output_path)

if __name__ == '__main__':
    main()
