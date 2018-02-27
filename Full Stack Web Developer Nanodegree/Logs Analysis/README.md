# Logs Analysis Project
## Contents
- Logs_Analysis.py - source code to generate log analysis report.
- sample_report.txt - An example of program's output.

## Environment Requirements
- Python 2.7 or above (tested on Python 2.7 and 3.5.2).
- [Virtual Machine from the class], or you can config your own environment referring to the virtual machine settings if you are an expert. 
- [Data set for the project], imported to your PostgreSQL database. 

## How To Run
Download, unzip, and execute Logs_Analysis.py in your Vagrant VM:
```sh
python Logs_Analysis.py
```
It should print out a report with the three required sections. 

The program support two arguments. Use *-a* to specify the number of articles and *-u* to specify number of authors. Default values are 3 articles and 4 authors according to project instruction. Example use:
```sh
python Logs_Analysis.py -a 10 -u 5
# print out top-10 articles with most views and top-5 most popular authors
```
If you want to generate a txt report, simply redirect the output to a file:
```sh
python Logs_Analysis.py > report_file.txt
```

## Database Views 

**You do not have to manually create these views** since the program already includes such SQLs. But if you are interested... Here is the code to create the view here for reference.

##### V_ARTICLE_AUTHOR
Join articles with authors to know who wrote what. 
```SQL
create or replace view v_article_author as
    select ar.*, au.name, au.bio
    from articles ar
    left join authors au
    on ar.author=au.id;
```

##### V_ARTICLE_LOG
Join logs with articles to count page views. 
```SQL
create or replace view v_article_log as
    select log.path, log.ip, log.method, log.status,
         log.time as visit_time, log.id as log_id, aa.*
    from log
    left join v_article_author aa
    on aa.slug=substr(path,10,1000)
```

##### V_DAILY_LOG
HTTP requests count group by day. 
```SQL
        create or replace view v_daily_log as
        select to_char(time, 'Mon dd, yyyy') day_mon,
        count(1) all_requests, 
        count(case when substr(status,1,1) in ('4','5') then 1 
              else null end) error_requests, 
        count(distinct ip) distinct_ip
        from log group by to_char(time,'Mon dd, yyyy');
```

## Program Design
SQL codes above clearly shows the design idea of programming. After the views are created, it is simple to query the view with criteria to get the log analysis results.

Because different types of results can be output in a similar format, I write a procedure that firstly queries the data and then formats the data. When formatting I try to use tabs so that it is easier to paste into a spreadsheet.

#####PS:
*This is not required by the project, but I found that logs are very suspicious, as count(distinct IP) results show that there are EXACTLLY 762 visitors EVERYDAY. Could be made up less fake...*

[Virtual Machine from the class]: https://classroom.udacity.com/nanodegrees/nd004/parts/8d3e23e1-9ab6-47eb-b4f3-d5dc7ef27bf0/modules/bc51d967-cb21-46f4-90ea-caf73439dc59/lessons/5475ecd6-cfdb-4418-85a2-f2583074c08d/concepts/14c72fe3-e3fe-4959-9c4b-467cf5b7c3a0
[Data set for the project]: https://d17h27t6h515a5.cloudfront.net/topher/2016/August/57b5f748_newsdata/newsdata.zip