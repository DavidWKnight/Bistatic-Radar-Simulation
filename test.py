from multiprocessing import Pool

coef = 3

def f(x):
    return x*coef

if __name__ == '__main__':
    with Pool(5) as p:
        print(p.map(f, [1, 2, 3]))
