
def detect(expression):
    alpha = list()
    symbol = list()
    temp_sym = expression[0]
    for i in range(1, len(expression)):
            if expression[i].isalpha():
                temp_sym += expression[i]
                if i == len(expression) - 1:
                    alpha.append(temp_sym)
                    temp_sym = ''
            else:
                if temp_sym != '':
                    alpha.append(temp_sym)
                symbol.append(expression[i])
                temp_sym = ''
    return alpha, symbol

test_req = 'mouse & horse'
print(detect(test_req))