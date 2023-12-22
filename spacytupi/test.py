import conjugation as cj
import tupi

print("hello 'ary gûé!")

verbo = tupi.Verb("kutuk","v.tr.","falar")
verbo_ero = tupi.Verb("eroîeupir","ero","levar")
adjetivo = tupi.Verb("oryb","adj (s)","feliz")
print(cj.table_indicativo(verbo) )
print(cj.table_indicativo(adjetivo))
print(cj.table_indicativo(verbo_ero) )


print(cj.table_permissivo(verbo) )
print(cj.table_permissivo(adjetivo))
print(cj.table_permissivo(verbo_ero) )