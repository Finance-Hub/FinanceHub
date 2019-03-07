# Contributing to FinanceHub
First off, thanks for taking the time to contribute.

The following are guidelines (not rules) for contributing to FinanceHub
repository. Use your best judgement and feel free to propose changes.

## What to do before you start

**Our objective is to have data and tools that remove costs from the
research process**. That is why the FinanceHub project is intentionally
very modular. Nearly everything you are going to interact with comes
from a subpackage. For example, building trackers for specific assets
classes or grabbing data from a specific source. That is why we favor
codes that wrap around a general case.

**Learn what you are getting yourself into**. Explore the project.
Have a look inside the files that already are in the repository. They
can be used for style reference and even for learning. Build your code
with the same style as the ones you see in the repository, this will
help to ease the understanding for newcomers and motivate contributions
with the same guidelines.

**MOST IMPORTANTLY: Remember you are not writing code for yourself**.
Contributing means that you are writing code for other people to
understand and use, and it has to run on different computers. Keep your
code clean, concise and do your best to make it efficient. Code
organization and readability are important to keep the workflow
productive and less frustrating. Basically, if you do not have the time
to organize your code, we will not have the time to read it and test it.


## Design Decisions

* **We speak python**. This repository is soon going to be a library, a
package, and for that to work it has to be written in a single language.
Contributions in other programming languages will not be accepted.
"The Zen of Python" guidelines applies to this project. If you do not
know what that is, open your python console and run `import this`.

* **The general case allows for scalability**. We favor code that allows
the same functionality for several cases. This avoids the need to
change specific lines in scripts, makes the actual work less code
intensive and allows for other people to use the same functionality. In
summary, *python classes are better than python scripts*.

* **Code needs documentation**. A few short lines explaining what you
did goes a long way for helping other people understand and use your
code. If you want to go the extra mile, create an example file with
applications of your code.

* **Code style helps with readability and testing**. We follow the
[PEP8](https://www.python.org/dev/peps/pep-0008/) guidelines, but not
strictly. Code organization and readability are important to keep the
workflow productive and less frustrating. Again, if you do not have
the time to organize your code, we will not have the time to read it
and test it.

## Bug Reports

* Bug reports are handled by the GitHub's issues tab of the project.
* **Debug the code**. You might find the problem yourself and then
submit a request for a correction instead of a bug report.

* Your bug report **must contain**:
    * Clear and descriptive title to identify the problem.
    * Description of the exact steps which reproduce the problem in as many details as possible.
    * Versions of the packages you are using.
    * Code for replication of the problem.
    * Explanation of which behaviour you expected to see and why.
    * Screenshots, if possible.

# Websites Worth Reading
 * **[Opensource.guide](https://opensource.guide/)**: GitHub's guide to open
 source projects.
