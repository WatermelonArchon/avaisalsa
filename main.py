# вариант 4 S
from parser import Parser

def main():
    p = Parser("https://www.aviasales.by/search/MSQ3010SYX1")
    try:
        p.run()
        print("Итого билетов:", len(p.tickets_list))
    finally:
        p.save_tickets("tickets.csv")
        p.save_function_logs("function_logs.csv")
        p.close()

if __name__ == "__main__":
    main()
    