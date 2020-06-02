# -*- coding: utf-8 -*-

#
# Tanaus\'u del Pino Alem\'an
#
# Sudoku solver
#

import sys, copy

# Main:
def main():
    ''' Solves Sudokus
    '''

    # Argument check
    if len(sys.argv) < 2:
        msg = '# Error: You must specify an input file.\n' + \
              'Usage: python Sudoku.py sudoku_file'
        sys.exit(msg)
    else:
        try:
            f = open(sys.argv[1],'r')
            inp = list(f)
            f.close()
        except:
            msg = '# Error: You must specify an input file.\n' + \
                  'Usage: python Sudoku.py sudoku_file'
            sys.exit(msg)

    # Read Sizes
    Siz = inp[0]
    inp = inp[1:len(inp)]
    Siz = Siz.split(',')
    try:
        NS = int(Siz[0].strip())
    except:
        sys.exit('# Error: First line in input must be ' + \
                 '"number of BIG squares per side, number' + \
                 ' of small squares per BIG square side"')
    try:
        NC = int(Siz[1].strip())
    except:
        sys.exit('# Error: First line in input must be ' + \
                 '"number of BIG squares per side, number' + \
                 ' of small squares per BIG square side"')
    if len(inp) < NC*NS:
        sys.exit('# Error: The are less input lines than' + \
                 'you specified')

    # Define the grid
    grid = grid_class(NS, NC)

    # Read the input
    icell = 0
    for i in range(grid.Nrow):
        line = inp[i].split(',')
        for lin in line:
            lin = lin.strip()
            if lin != '':
                grid.cell[icell].fix = 1
                grid.unknown.remove(icell)
                grid.cell[icell].ori = 1
                try:
                    lin = int(lin)
                except ValueError:
                    sys.exit('# Error: One of the inputs is ' + \
                             'not an integer')
                except:
                    raise
                if lin < 0 or lin > NS*NC:
                    sys.exit('# Error: The integers must be ' + \
                             'larger than 0 and, for this ' + \
                             'size, lesser than '+str(NS*NC))
                grid.cell[icell].val.append(int(lin))
            icell += 1

    # Show initial game
    for i in range(grid.Nrow*2 + 1):
        print ''
    grid.draw()

    # Initialize posibilities
    grid.init()

    # Do the guesses that are clear and give them the green flag
    check = grid.guess()
    if not check:
        sys.exit(' - I could not find a solution - ')
    grid.soften()
    grid.draw()

    # Check if solved with the simple method
    check = grid.check()
    if check:
        sys.exit(' - Problem solved - ')

    # If not solved, you have to use brute force
    check = brute_force(grid)
    if check:
        sys.exit(' - Problem solved - ')
    else:
        sys.exit(' - I could not find a solution - ')


class grid_class:
    ''' Stores squares, rows, columns and indexes
    '''

    def __init__(self, NS, NC):
        ''' Initializator of grid
        '''

        # Dimensions
        self.NS = NS
        self.NC = NC
        self.Ns = NS*NS
        self.Ncps = NC*NC
        self.Nrow = NC*NS
        self.Ncol = self.Nrow
        self.Ncell = NC*NS*NC*NS
        self.Ssize = self.Nrow/10 + 1

        # Grid indexation inicialization
        self.square = []
        for i in range(NS*NS):
            self.square.append([])
        self.row = []
        self.column = []
        for i in range(NC*NS):
            self.row.append([])
            self.column.append([])
        self.cell = []
        self.depend = []

        # Build grid indexation
        isqr = 0 ; irsqr = 0 ; icsqr = 0 ; iasqr = 0
        irow = 0 ; iarow = 0
        icol = 0
        for i in range(self.Ncell):
            self.square[isqr].append(i)
            self.row[irow].append(i)
            self.column[icol].append(i)
            self.cell.append(cell_class(i,isqr,irow,icol,val=[]))
            icsqr += 1
            iarow += 1
            icol += 1
            if icsqr == self.NC:
                icsqr = 0
                isqr += 1
                iasqr += 1
                if iasqr == self.NS:
                    irsqr += 1
                    iasqr = 0
                    if irsqr == self.NC:
                        irsqr = 0
                    else:
                        isqr -= self.NC
            if iarow == self.Nrow:
                iarow = 0
                irow +=1
            if icol == self.Ncol:
                icol = 0

        # Get the dependences for each file
        for i in range(self.Ncell):
            lst = []
            for j in self.row[self.cell[i].irow]:
                lst.append(j)
            for j in self.column[self.cell[i].icol]:
                lst.append(j)
            for j in self.square[self.cell[i].isqr]:
                lst.append(j)
            self.depend.append(unique(lst))

        # List of unsolved cells
        self.unknown = range(self.Ncell)



    def draw(self):
        ''' Print the game on screen '''

        # ANSI codes
        CURSOR_UP_ONE = '\x1b[1A'
        ERASE_LINE = '\x1b[2K'
        normal = '\033[0m'
        green = '\033[92m'
        bold = '\033[1m'
        blue = '\033[94m'
        red = '\033[91m'
        separator = ''

        # Erase screen
        print (CURSOR_UP_ONE+ERASE_LINE+CURSOR_UP_ONE)*(self.Nrow+1)

        # Print the grid
        for j in range(self.Ncol):
            separator += ' ' + '-'*(self.Ssize + 1)
        print separator
        form = '{0:'+str(self.Ssize)+'d}'
        for i in range(self.Nrow):
            for j in range(self.Ncol):
                if self.cell[i*self.Nrow + j].fix == 1:
                    if self.cell[i*self.Nrow + j].ori == 1:
                        val = form.format(self.cell[i*self.Nrow + j].val[0])
                        val = blue+bold+val+normal
                    else:
                        val = form.format(self.cell[i*self.Nrow + j].val[0])
                        if self.cell[i*self.Nrow + j].soft:
                            val = green+val+normal
                        else:
                            val = red+val+normal
                else:
                    val = ' '*self.Ssize
                print '|'+val,
            print '|'
            print separator



    def init(self):
        ''' This initialices the possible values in the unknowns
        '''

        # For each cell, check what are the possible values
        # from the initial condition
        for i in self.unknown:
            val = 0
            while True:
                val += 1
                if val > self.Ncps:
                    break
                for k in self.depend[i]:
                    if self.cell[k].fix == 0:
                        continue
                    if val in self.cell[k].val:
                        val += 1
                        continue
                if val > self.Ncps:
                    break
                self.cell[i].val.append(val)



    def update(self, ind):
        ''' This updates the dependent cells. Returns True if the
            cell value is valid (at that moment), False if not
        '''

        # Take the value to remove
        val0 = self.cell[ind].val[0]

        # And remove it
        for j in self.depend[ind]:
            if j == ind:
                continue
            if val0 in self.cell[j].val:
                self.cell[j].val.remove(val0)
                # If it gets empty, something went wrong
                if len(self.cell[j].val) < 1:
                    return False
        return True



    def guess(self):
        ''' Make the best guess that it can from the known data
        '''

        # Start the loop
        while True:
            update = 0
            # For each cell
            for cell in self.cell:
                if cell.fix == 1:
                    continue
                # Check if can only have one value
                if len(cell.val) == 1:
                    cell.fix = 1
                    self.unknown.remove(cell.icell)
                    update = 1
                    check = self.update(cell.icell)
                    if not check:
                        return False
                    self.draw()
                    continue
                # Check unique values with respect with the rest
                # of the column
                for val in cell.val:
                    found = 0
                    for j in self.column[cell.icol]:
                        if cell.icell == self.cell[j].icell:
                            continue
                        if val in self.cell[j].val:
                            found = 1
                            break
                    if found == 1:
                        continue
                    cell.val = [val]
                    cell.fix = 1
                    self.unknown.remove(cell.icell)
                    update = 1
                    check = self.update(cell.icell)
                    if not check:
                        return False
                    self.draw()
                    break
                if update == 1:
                    continue
                # Check unique values with respect with the rest of
                # the row
                for val in cell.val:
                    found = 0
                    for j in self.row[cell.irow]:
                        if cell.icell == self.cell[j].icell:
                            continue
                        if val in self.cell[j].val:
                            found = 1
                            break
                    if found == 1:
                        continue
                    cell.val = [val]
                    cell.fix = 1
                    self.unknown.remove(cell.icell)
                    update = 1
                    check = self.update(cell.icell)
                    if not check:
                        return False
                    self.draw()
                    break
                if update == 1:
                    continue
                # Check unique values with respect with the rest of
                # the square
                for val in cell.val:
                    found = 0
                    for j in self.square[cell.isqr]:
                        if cell.icell == self.cell[j].icell:
                            continue
                        if val in self.cell[j].val:
                            found = 1
                            break
                    if found == 1:
                        continue
                    cell.val = [val]
                    cell.fix = 1
                    self.unknown.remove(cell.icell)
                    update = 1
                    check = self.update(cell.icell)
                    if not check:
                        return False
                    self.draw()
                    break
            if update == 0:
                break
        return True



    def check(self):
        ''' Checks if everything is fixed already
        '''


        # Check if everything is fixed
        for cell in self.cell:
            if cell.fix == 0:
                return False
        return True



    def soften(self):
        ''' Flags the fixed
        '''

        # Check if everything is fixed
        for cell in self.cell:
            if cell.fix == 1:
                cell.soft = 1



class cell_class:
    ''' A cell is each of the little squares in the game
    '''

    def __init__(self, icell, isqr, irow, icol, fix = 0, \
                 ori = 0, val = [ ], soft = 0):
        ''' The initialization '''

        self.icell = icell
        self.isqr = isqr
        self.irow = irow
        self.icol = icol
        self.ori = ori
        self.fix = fix
        self.val = val
        self.soft = soft



def brute_force(grid):
    ''' This solves by brute force the remaining system
    '''

    # For each cell that is not yet known
    for i in grid.unknown:
        cell = grid.cell[i]
        ran = copy.deepcopy(cell.val)
        # Try for each of the values
        for val in ran:
            cgrid = copy.deepcopy(grid)
            cgrid.cell[cell.icell].fix = 1
            cgrid.unknown.remove(cell.icell)
            cgrid.cell[cell.icell].val = [val]
            # If the value is not valid, remove it and go to the next
            check = cgrid.update(cell.icell)
            if not check:
                cell.val.remove(val)
                if len(cell.val) < 1:
                    return False
                continue
            # Try to solve the problem by direct method, if find that
            # the solution is not valid, erase this value
            check = cgrid.guess()
            if not check:
                cell.val.remove(val)
                if len(cell.val) < 1:
                    return False
                continue
            # Check if the problem is already solved
            check = cgrid.check()
            if check:
                return True
            # If you could not solve it, try brute force recursively
            else:
                check = brute_force(cgrid)
                # If you failed again, the value is not the solution
                if not check:
                    cell.val.remove(val)
                    if len(cell.val) < 1:
                        return False
                    continue
                else:
                    return True
    # If you reached this return, there ir no solution for the input
    # grid
    return False



def unique(lst):
    ''' Returns a list without duplicates
    '''

    out = []
    for ele in lst:
        if ele not in out:
            out.append(ele)
    return out



if __name__ == "__main__":
    main()
