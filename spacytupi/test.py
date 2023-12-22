import conjugation as cj
import tupi

print("hello 'ary gûé!")

verbos = [tupi.Verb("poroîuká","v.","falar"),
          tupi.Verb("porombo'e","v.","falar"),
          tupi.Verb("mba'epe'a","v.","falar"),
          tupi.Verb("mba'e'u","v.","falar"),
          tupi.Verb("porabyky","v.","falar"),
          tupi.Verb("moroekar","v.","falar"),
          tupi.Verb("mba'eepîak","v.","falar"),
          tupi.Verb("pab","v.","falar"),
          tupi.Verb("kanhem","v.","falar"),
          tupi.Verb("nhan","v.","falar"),
          tupi.Verb("nhe'eng","v.","falar"),
          tupi.Verb("manõ","v.","falar"),
          tupi.Verb("nhe'engĩ","v.","falar")
          ]
verbo_ero = tupi.Verb("eroîeupir","ero","levar")
adjetivo = tupi.Verb("oryb","adj (s)","feliz")
#print(cj.table_indicativo(verbo) )
#print(cj.table_indicativo(adjetivo))
#print(cj.table_indicativo(verbo_ero) )

for v in verbos:
    print(cj.table_gerundio(v))