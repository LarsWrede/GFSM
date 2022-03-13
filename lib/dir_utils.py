import getpass

def get_local_git_uri():
    user = getpass.getuser()
    if user == 'dennisblaufuss':
        local_git_link = '/Users/dennisblaufuss/Desktop/Uni/Repos/GFSM'
    if user == 'Lars':
        local_git_link = '/Users/dennisblaufuss/Desktop/Uni/Repos/GFSM'
    if user == 'sophiemerl':
        local_git_link = '/Users/sophiemerl/Desktop/GSFM/T10/GFSM'
    if user == 'nicol':
        local_git_link = 'C:\\Users\\nicol\\git\\GFSM'
    if user == 'nicolaskepper':
        local_git_link = '/Users/nicolaskepper/git/GFSM'
    if user == 'Phillip':  # lol
        local_git_link = '/Users/dennisblaufuss/Desktop/Uni/Repos/GFSM'
    return local_git_link

def get_directory_delimiter():
    user = getpass.getuser()
    if user == 'dennisblaufuss':
        return '/'
    if user == 'Lars':
        return '/'
    if user == 'sophiemerl':
        return '/'
    if user == 'nicol':
       return '\\'
    if user == 'nicolaskepper':
        return '/'
    if user == 'Phillip':  # lol
        return '/'