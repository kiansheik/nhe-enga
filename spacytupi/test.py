import conjugation as cj
import tupi

print("hello 'ary gûé!")

verbo = tupi.Verb("kutuk","v.tr.","falar")
adjetivo = tupi.Verb("oryb","adj (s)","feliz")
print(cj.table_indicativo(verbo) )
print(cj.table_indicativo(adjetivo))

print(cj.table_permissivo(verbo) )
print(cj.table_permissivo(adjetivo))