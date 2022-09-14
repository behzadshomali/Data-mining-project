# Data Mining course projects

This repository contains our joint work (Mohammad Mohammadzadeh and I) in the context of the "Introduction to Data Mining" course (held at the Ferdowsi University of Mashhad) projects. We were supposed to do the projects in several phases, which are as follows: 

1. [Data crawling](#phase-1-data-crawling)

## Phase 1: Data crawling
In this phase, we should first select a university as our crawling target. Next, we should extract course information from the course catalog pages and then collect the course information according to the description. We finally chose <i>The University of Technology Sydney (UTS)</i>.

<p align="center">
<img src="./figures/uts_webpage.png">
</p>

In our codes, we had to inherit from the given class `BaseCrawler` which was an interface for our codes. We used the `requests` and `BeautifulSoup` modules to crawl and parse the web pages. Additionally, to speed up the process, the code works with multi-threads (`threads_count=<INTENDED_THREADS_NUM>`).

On our target website, for most of the courses, the following information was provided: 

* Projects
* Scores
* Prerequisite
* Objective
* Description
* Course title
* Department name
* Outcome
* References

The output of this phase was a `CSV` file containing all the crawled courses (rows), as well as their information (columns).