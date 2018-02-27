#!/usr/bin/env python
#
# Log_Analysis.py - nd004 Project
# by Luda Miao
#

import sys
import psycopg2

create_view_sql = """
        create or replace view v_article_author as
        select ar.*, au.name, au.bio
        from articles ar
        left join authors au
        on ar.author=au.id
        ;

        create or replace view v_article_log as
        select log.path, log.ip, log.method, log.status,
             log.time as visit_time, log.id as log_id, aa.*
        from log
        left join v_article_author aa
        on aa.slug=substr(path,10,1000)
        ;

        create or replace view v_daily_log as
        select to_char(time, 'Mon dd, yyyy') day_mon,
        count(1) all_requests,
        count(case when substr(status,1,1) in ('4','5') then 1
              else null end) error_requests,
        count(distinct ip) distinct_ip
        from log group by to_char(time,'Mon dd, yyyy');
        """

query = {
    "popular_articles":
        """
        select title, count(*)
        from v_article_log
        where title is not null
        group by title
        order by count(*) desc
        limit {};
        """,
    "popular_author":
        """
        select name author_name , count(*)
        from v_article_log
        where name is not null
        group by name
        order by count(*) desc
        limit {};
        """,
    "error_days":
        """
        select day_mon,
            to_char(round(error_requests*100.0/all_requests,2),'999D99%') rate
        from v_daily_log
        where all_requests>0
              and error_requests*1.0/all_requests>0.01
        ;
        """,
    "log_range":
        """
        select min(time) min_time, max(time) max_time
        from log
        ;
        """
}


def get_argv():
    """
    get argv for top N articles(-a) and/or authors(-u).
        usage: $ python3 Log_Analysis.py -a 3 -u 4
        argvs:
             -a N: top N most popular articles.
             -u N: top N most popular authors.
    """
    args = sys.argv
    # sys.argv, no need for additional modules.
    a, u = 3, 4
    # default top 3 authors and top 4 articles.
    try:
        whole_args = " ".join(args)
        if len(args) == 1:
            return 3, 4
        if whole_args.find("-a") < 0 and whole_args.find("-u") < 0:
            print("# Undefined Argument, use default (3 authors, 4 articles)")
            return 3, 4
        if len(args) < 5:
            a = int(args[2]) if args[1][1] == "a" else 3
            u = int(args[2]) if args[1][1] == "u" else 4
        if len(args) >= 5:
            if args[1][1] == "a":
                a = int(args[2])
            else:
                if args[3][1] == "a":
                    a = int(args[4])
            if args[1][1] == "u":
                u = int(args[2])
            else:
                if args[3][1] == "u":
                    u = int(args[4])
        return a, u
    except (NameError, ValueError, TypeError):
        print("# Undefined Argument, use default (3 authors, 4 articles)")
        return 3, 4


def query_and_print(print_type, db_cursor, sql, sql_arg=""):
    """
        Query data and print out in plain txt.
        input:
            print_type: views or errors in string
            db_cursor: pass in db.cursor for execution.
            sql: SQL in string
            sql_argv: argument that pass into SQL
        output:
            print a list of formatted data.
    """
    db_cursor.execute(sql.format(sql_arg))
    rows = db_cursor.fetchall()
    for i in rows:
        print("\t{}\t-\t{} {}".format(i[0], i[1], print_type))
    print("")


if __name__ == "__main__":
    a, u = get_argv()

    db = psycopg2.connect("dbname=news")
    c = db.cursor()

    c.execute(create_view_sql)
    # create/update view all at once

    print("## Log Analysis for date range:")
    query_and_print("", c, query["log_range"], a)
    print("#### Start of Report ####")

    print("Top {} Most Popular Articles: ".format(a))
    query_and_print("views", c, query["popular_articles"], a)

    print("Top {} Most Popular Authors: ".format(u))
    query_and_print("views", c, query["popular_author"], u)

    print("Days more than 1% requests lead to HTTP errors (4XX or 5XX): ")
    query_and_print("errors", c, query["error_days"])

    c.close()

    print("#### End of Report ####")
