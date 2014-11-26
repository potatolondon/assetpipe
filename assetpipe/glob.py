
import os
import re

def touch(fname, times=None):
    with file(fname, 'a'):
        os.utime(fname, times)

def glob(pathname):
    """
    >>> import os
    >>> try:
    ...     os.makedirs("/tmp/globber/1/2/3")
    ... except:
    ...     pass
    >>> touch("/tmp/globber/a.py")
    >>> touch("/tmp/globber/1/a.py")
    >>> touch("/tmp/globber/1/2/a.py")
    >>> touch("/tmp/globber/1/2/c.txt")
    >>> touch("/tmp/globber/1/2/3/a.py")
    >>> touch("/tmp/globber/1/2/3/b.txt")
    >>> touch("/tmp/globber/1/2/3/b a.csv")
    >>> glob("/tmp/globber/*.py")
    ['/tmp/globber/a.py']
    >>> glob("/tmp/globber/**/*.py")
    ['/tmp/globber/a.py', '/tmp/globber/1/a.py', '/tmp/globber/1/2/a.py', '/tmp/globber/1/2/3/a.py']
    >>> glob("/tmp/globber/**/2/**/*.py")
    ['/tmp/globber/1/2/a.py', '/tmp/globber/1/2/3/a.py']
    >>> glob("/tmp/globber/**/2/**/*.csv")
    ['/tmp/globber/1/2/3/b a.csv']
    """

    results = []

    root = os.path.dirname(pathname).split("**")[0]
    regex = re.escape(pathname)

    regex = regex.replace("\\*\\*\\/\\*", "([a-zA-Z0-9_-|\\/|\s]+)")
    regex = regex.replace("\\*\\*", "([a-zA-Z0-9_-|\\/|\s]+)")
    regex = regex.replace("\\*", "([a-zA-Z0-9_-]+)")

    for root, dirnames, filenames in os.walk(top=root, followlinks=True):
        for f in filenames:
            full_path = os.path.join(root, f)
            if re.match(regex, full_path):
                results.append(full_path)

    return results


if __name__ == '__main__':
    import doctest
    doctest.testmod()

