import re


def checksum(string):
    digits = list(map(int, string))
    odd_sum = sum(digits[-1::-2])
    even_sum = sum([sum(divmod(2 * d, 10)) for d in digits[-2::-2]])
    return ((odd_sum + even_sum) % 10 == 0)


if __name__ == '__main__':
    # Fichero con tarjetas cada una en una nueva linea
    cc_path = 'cc.txt'
    # Fichero con los patrones a buscar en el formato [tipo,expresionregular] en cada nueva linea
    regex_path = 'regexcard.csv'

    # Importamos los patrones en una lista
    regex_list = []
    with open(regex_path, 'r') as regex_file:
        for line in regex_file:
            line_list = line.rstrip().split(',')
            regex_list.append(line_list)

    with open(cc_path, 'r') as cc_file:
        # Recorremos cada numero de tarjeta
        for cc in cc_file:
            # Creamos una lista por cada numero de tarjeta
            cc_list = cc.rstrip().split()
            # Verificamos el luhn
            if checksum(cc.rstrip()):
                cc_list.append("Luhn")
            else:
                cc_list.append("Not_luhn")
            # Recorremos todos los patrones para cada numero de tarjeta
            for regEx in regex_list:
                # print(regEx[1].rstrip())
                # if re.search(regEx[1].rstrip(), cc) is not None:
                if re.search(r"%s" % regEx[1].rstrip(), cc) is not None:
                    # Si hay match con la expresion regular, añadimos el tipo de dicho match
                    cc_list.append(regEx[0])
                else:
                    # Si no hay match, se añade columna en blanco para tratar fichero
                    cc_list.append("")
            # Imprimimos quitando los operadores de lista
            print(', '.join(cc_list))
