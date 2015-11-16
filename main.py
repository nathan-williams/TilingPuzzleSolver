#!/usr/bin/python
from game import *
from random import choice
import threading
from itertools import permutations, islice
from math import factorial
import time
from PIL import ImageGrab
import os, inspect
import canvasvg

def getGridOfTileLocationsOnBoard(game,export):
	"""
	Creates a grid containing the tileGroup occupying each space in the grid.

	:param game: the game containing board and tile information
	:type game: Game
	:param export: dictionary of tuples(row,col,x,y,spawned,gridIndex) describing each of the tiles' states
	:type export: dict<int,tuple(int,int,int,int,bool,int)>
	:returns: a 2-D array similar to the board; each cell in the grid is None, if no tile is occupying that space, or a tileKey
	:rtype: 2-D array
	"""
	tileGroups = game.tileBucket.tileGroups
	tiles=game.tileBucket.tiles
	tileLocationsByGroup = {tileGroup:set([export[tileKey] for tileKey in tileGroup]) for tileGroup in tileGroups}
	tileLocationsOnBoard = [[None for c in r] for r in game.board.grid]
	for tileGroup in tileGroups:
		for tileInfo in tileLocationsByGroup[tileGroup]:
			r,c,x,y,s,i = tileInfo
			grid = tiles[tileGroup[0]].distinctGrids[i]
			for dr in range(len(grid)):
				for dc in range(len(grid[0])):
					tileLocationsOnBoard[r+dr][c+dc] = tileGroup if grid[dr][dc] != ' ' else None
	return tileLocationsOnBoard

def duplicateSolution(game,export):
	"""
	Determines whether the solution desribed by export has already been found.

	:param game: the game containing board and tile information
	:type game: Game
	:param export: dictionary of tuples(row,col,x,y,spawned,gridIndex) describing each of the tiles' states
	:type export: dict<int,tuple(int,int,int,int,bool,int)>
	:returns: True if a solution equivalent to that described by export is already in game.solutions
	:rtype: 2-D array
	"""
	if len(game.solutions) == 0:
		return False
	tileGroups = game.tileBucket.tileGroups
	tiles = game.tileBucket.tiles
	gridOfTileLocationsOnBoardA = getGridOfTileLocationsOnBoard(game,export)
	for solution in game.solutions:
		gridOfTileLocationsOnBoardB = getGridOfTileLocationsOnBoard(game,solution)
		for n in range(4):
			gridOfTileLocationsOnBoardB = rotateClockwise(gridOfTileLocationsOnBoardB)
			if equivalentGrids(gridOfTileLocationsOnBoardA,gridOfTileLocationsOnBoardB):
				return True
		gridOfTileLocationsOnBoardB = flipHorizontally(gridOfTileLocationsOnBoardB)
		for n in range(4):
			gridOfTileLocationsOnBoardB = rotateClockwise(gridOfTileLocationsOnBoardB)
			if equivalentGrids(gridOfTileLocationsOnBoardA,gridOfTileLocationsOnBoardB):
				return True
	return False

def permute(game,tileList,index,startrow=0,startcol=0):
	"""
	Find solutions by permuting through orders of tielList.

	:param game: the game containing board and tile information
	:type game: Game
	:param tileList: the list of tiles
	:type tileList: list(Tile)
	:param index: index of tileList to focus on where you should keep permuting from
	:type index: int
	:param startrow: the row to start scanning from; defaults to 0
	:type startrow: int
	:param startcol: the col to start scanning from; defaults to 0
	:type startcol: int
	:returns: True if tileList is a solution
	:rtype: bool
	"""
	board = game.board
	if index == len(tileList):
		export = game.tileBucket.export()
		if not duplicateSolution(game,export):
			game.solutions.append(game.tileBucket.export())
			# do not redraw solutions if more than 100 solutions
			# the rest can be drawn manually by invoking the [Draw Solutions] button
			if len(game.solutions) <= game.maxSolnsDrawn:
				game.readyToDrawSolutions = True
			return True
	else:
		for i in range(index,len(tileList)):
			tile = tileList[i]

			# if a solution may exist on this branch, continue permuting
			# otherwise, cut the branch
			for n in range(len(tile.distinctGrids)):
				grid = tile.distinctGrids[n]
				row,col = board.nextEmptySpace(startrow,startcol)

				tile.grid = grid

				colShift = 0
				for c in range(len(tile.grid[0])):
					if tile.grid[0][c] == ' ':
						colShift += 1
					else:
						break

				if board.validMove(tile,row,col-colShift): # not a bad branch
					board.placeTile(tile,row,col-colShift)

					if game.animate.get():
						game.tileInfo = game.tileBucket.export()

					tl = tileList[0:index]+[tile]+tileList[index:i]+tileList[i+1:]
					solutionFound = permute(game,tl,index+1,row,col)
					board.removeTile(tile)

					if game.animate.get():
						game.tileInfo = game.tileBucket.export()
	return False

def bruteForce(game):
	"""
	Find solution(s) with brute force method. All possible permutations of the tile list are tried out.
	The idea was that the tiles could be placed in a well-defined and consistent fashion if the left-most space of the top row of the tile is aligned with the (row,col) of the tile.
	By this method, only certain orderings of the tiles will result in a filled board.
	Branches could be cut whenever the tile in its current position in the permutation.

	:param game: the game containing board and tile information
	:type game: Game
	"""
	start_time = time.time()

	game.clearBoard()
	game.solutions = []
	tiles = game.tileBucket.tiles
	tileList = [tiles[x] for x in tiles]
	permute(game,tileList,0)
	game.readyToDrawSolutions = True

	stop_time = time.time()
	print 'Execution time:  ' + str(stop_time-start_time)
	print 'Solutions found: ' + str(len(game.solutions))
	print ''

def cleanConstraints(game,boardConstraints,tileConstraints,move):
	"""
	Updates the constraint lists so that moves that have become invalid after some move was executed are no longer present. These moves may have become invalid because the tile was played already or the tile consumed that space on the board.

	:param game: the game containing board and tile information
	:type game: Game
	:param boardConstraints: contains a constraint for each unoccupied board space; key values are (row,col) pairs corresponding to unoccupied board spaces; values are lists of possible moves in the form of (tileGroup,row,col,gridIndex)
	:type boardConstraints: dict<tuple(int,int),list((tuple,int,int,int))>
	:param tileConstraints: contains a constraint for each tile; key values are tileGroups; values are lists of possible moves in the form (row,col,gridIndex)
	:type tileConstraints: dict<tuple(int,int,...),list((int,int,int))>
	:param move: describes the move to be executed of the form (tileGroup,row,col,gridIndex)
	:type move: tuple(tuple,int,int,int)
	:returns: True if there is a possible move to satisfy every board constraint; False if there is a board constraint that cannot be satisfied with any available tiles
	:rtype: bool
	"""
	placedTileGroup,gridIndex,row,col = move
	placedTile = placedTileGroup[0]
	newTileGroup = tuple(y for y in placedTileGroup if y != placedTile)
	board = game.board
	tiles = game.tileBucket.tiles
	tile = tiles[placedTile]

	# remove board spaces that were filled by the placed tile in boardConstraints
	filledSpaces = []
	for dr in range(len(tile.grid)):
		for dc in range(len(tile.grid[0])):
			if tile.grid[dr][dc] != ' ':
				# occurs if branching with multiple moves and moves conflict
				if (row+dr,col+dc) not in boardConstraints:
					return False
				del boardConstraints[(row+dr,col+dc)]
				filledSpaces.append((row+dr,col+dc))
	filledSpaces = set(filledSpaces)

	# POSSIBLE FUTURE IMPROVEMENT
	# remove moves that are just reflections / rotations
	# if board.horizontalSymmetry:
	# 	pass
	# if board.verticalSymmetry:
	# 	pass
	# for n in range(3):
	# 	if board.rotationalSymmetry[n]:
	# 		pass


	if (gridIndex,row,col) in tileConstraints[placedTileGroup]:
		# remove placed tile location from its tile gorup in tileConstraints
		tileConstraints[placedTileGroup].remove((gridIndex,row,col))
		# remove placed tile from its tile group in tileConstraints
		if len(newTileGroup) > 0:
			tileConstraints[newTileGroup] = tileConstraints[placedTileGroup]
		del tileConstraints[placedTileGroup]

	# remove placed tile from its tile groups in boardConstraints
	for coord in boardConstraints:
		constraint = boardConstraints[coord]
		for x in xrange(len(constraint)-1,-1,-1):
			tileGroup,gridIndex,row,col = constraint[x]
			if tileGroup == placedTileGroup:
				constraint[x] = (newTileGroup,gridIndex,row,col)
				if len(newTileGroup) == 0:
					del constraint[x]
					# bad branch; no tile can fill this space on the board
					if len(constraint) == 0:
						return False
	
	# remove possible tile positions in tileConstraints that are not possible anymore
	for tileGroup in tileConstraints:
		constraint = tileConstraints[tileGroup]
		for x in xrange(len(constraint)-1,-1,-1):
			gridIndex,row,col = constraint[x]
			tileKey = tileGroup[0]
			tile = tiles[tileKey]
			tile.grid = tile.distinctGrids[gridIndex]
			if not board.validMove(tile,row,col):
				del constraint[x]
				for dr in range(len(tile.grid)):
					for dc in range(len(tile.grid[0])):
						if tile.grid[dr][dc] != ' ' and (row+dr,col+dc) in boardConstraints:
							boardConstraints[(row+dr,col+dc)].remove((tileGroup,gridIndex,row,col))
							# bad branch; no tile can fill this space on the board
							if len(boardConstraints[(row+dr,col+dc)]) < 1:
								return False

	# remove tiles that cannot be placed anywhere anymore
	# note that this does not necessarily mean bad branch
	#     in the case that there are extra tiles
	tileConstraints = {tileGroup:tileConstraints[tileGroup] for tileGroup in tileConstraints if len(tileConstraints[tileGroup]) > 0}

	return True

def branch(game,boardConstraints,tileConstraints,move):
	"""
	Executes a move, updates the constraint lists, and continues branching if there is still at least one valid move to satisfy every board constraint.


	:param game: the game containing board and tile information
	:type game: Game
	:param boardConstraints: contains a constraint for each unoccupied board space; key values are (row,col) pairs corresponding to unoccupied board spaces; values are lists of possible moves in the form of (tileGroup,row,col,gridIndex)
	:type boardConstraints: dict<tuple(int,int),list((tuple,int,int,int))>
	:param tileConstraints: contains a constraint for each tile; key values are tileGroups; values are lists of possible moves in the form (row,col,gridIndex)
	:type tileConstraints: dict<tuple(int,int,...),list((int,int,int))>
	:param move: describes the move to be executed of the form (tileGroup,row,col,gridIndex)
	:type move: tuple(tuple,int,int,int)
	"""
	tileGroup,gridIndex,row,col = move

	tileKey = tileGroup[0]
	board = game.board
	tiles = game.tileBucket.tiles
	tile = tiles[tileKey]

	tile.grid = tile.distinctGrids[gridIndex]
	board.placeTile(tiles[tileKey],row,col)
	if game.animate.get():
		game.tileInfo = game.tileBucket.export()

	# update boardConstraints
	bcClone = {foo:[bar for bar in boardConstraints[foo]] for foo in boardConstraints}
	tcClone = {foo:[bar for bar in tileConstraints[foo]] for foo in tileConstraints}
	success = cleanConstraints(game,bcClone,tcClone,move)

	# continue dancing if not a bad branch
	solved = False
	if success:
		solved = dance(game,bcClone,tcClone)

	# revert board state
	board.removeTile(tiles[tileKey])
	if game.animate.get():
		game.tileInfo = game.tileBucket.export()

	if solved and game.findJustOne.get():
		return True

# check for duplicate solutions manually because when tiles aren't played, then duplicates appear
# It is probably possible to add an optimization for removing moves corresponding to
# rotations / flips / reflections of the entire board.
def dance(game,boardConstraints,tileConstraints):
	"""
	Dances through the board constraints looking for tile solutions. The next move is chosen using the list of possible moves for the constraint with the least number of possible moves.
	For each of those possible moves, a branch is spawned and explored. If the board can be filled with the other tiles besides the one that is
	being branched with, then we will still have to branch again after eliminating that tile.

	:param game: the game containing board and tile information
	:type game: Game
	:param boardConstraints: contains a constraint for each unoccupied board space; key values are (row,col) pairs corresponding to unoccupied board spaces; values are lists of possible moves in the form of (tileGroup,row,col,gridIndex)
	:type boardConstraints: dict<tuple(int,int),list((tuple,int,int,int))>
	:param tileConstraints: contains a constraint for each tile; key values are tileGroups; values are lists of possible moves in the form (row,col,gridIndex)
	:type tileConstraints: dict<tuple(int,int,...),list((int,int,int))>
	"""
	# reapeat until board has no empty slots that have to be filled
	if not boardConstraints:
		export = game.tileBucket.export()
		if not duplicateSolution(game,export):
			game.solutions.append(export)
			# do not redraw solutions if more than 100 solutions
			# the rest can be drawn manually by invoking the [Draw Solutions] button
			if len(game.solutions) <= game.maxSolnsDrawn:
				# # export svg of board
				# game.update()
				# n = game.selectedFile.get()
				# n = n[n.index(':')+2:]
				# f = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))+"\\solutions\\"+str(n)+"\\"+str(len(game.solutions))+".svg"
				# d = os.path.dirname(f)
				# try:
				#     os.stat(d)
				# except:
				#     os.mkdir(d)
				# canvasvg.saveall(f,game.canvas1)

				game.readyToDrawSolutions = True
		return True

	board = game.board
	tileBucket = game.tileBucket
	tiles = tileBucket.tiles
	tileGroups = tileBucket.tileGroups

	coord = min(boardConstraints, key = lambda c : len(boardConstraints[c])) # get boardConstraint with least number of candidates
	tileGroup = min(tileConstraints, key = lambda tg : len(tileConstraints[tg])/len(tg)) # get tileConstraint with least number of candidates per tileGroup memeber

	if len(tileConstraints[tileGroup]) > 0 and len(tileConstraints[tileGroup])/len(tileGroup) < len(boardConstraints[coord]):
		for gridIndex,row,col in tileConstraints[tileGroup]:
			solved = branch(game,boardConstraints,tileConstraints,(tileGroup,gridIndex,row,col))
			if solved and game.findJustOne.get():
				return True
		canSolveWithoutTile = len(boardConstraints) <= sum([tiles[tg[0]].size*len(tg) for tg in tileConstraints]) -  tiles[tileGroup[0]].size
		if canSolveWithoutTile:
			# remove the branch that was explored from constraint lists
			newTileGroup = tuple(y for y in tileGroup if y != tileGroup[0])
			if len(newTileGroup) > 0:
				tileConstraints[newTileGroup] = tileConstraints[tileGroup]
				boardConstraints = {c:[(m[0],m[1],m[2],m[3]) if m[0] != tileGroup else (newTileGroup,m[1],m[2],m[3]) for m in boardConstraints[c]] for c in boardConstraints}
			else:
				boardConstraints = {c:[(m[0],m[1],m[2],m[3]) for m in boardConstraints[c] if m[0] != tileGroup] for c in boardConstraints}
			del tileConstraints[tileGroup]
			for c in boardConstraints:
				if len(boardConstraints[c]) == 0:
					return
			solved = dance(game,boardConstraints,tileConstraints)
			if solved and game.findJustOne.get():
				return True
	else:
		for move in boardConstraints[coord]:
			solved = branch(game,boardConstraints,tileConstraints,move)
			if solved and game.findJustOne.get():
				return True

def createConstraintLists(game):
	"""
	Creates the initial constraint lists by compiling a list of all possible moves that can satisfy a certain constraint. A board constraints list, in which each constraint corresponds
	to a space on the board, and a tile constraint list, in which each constraint corresponds to a tile in the tile bucket, are both created.

	:param game: the game containing board and tile information
	:type game: Game
	:returns: the two dictionaries, boardConstraints and tileConstraints
	:rtype: tuple(dict,dict)
	"""
	board = game.board
	tiles = game.tileBucket.tiles
	tileGroups = game.tileBucket.tileGroups
	boardConstraints = {(r,c):[] for c in range(board.cols) for r in range(board.rows) if board.grid[r][c] != ' '}
	tileConstraints = {}
	for tileGroup in tileGroups:
		for r in range(len(board.grid)):
			for c in range(len(board.grid[0])):
				tileKey = tileGroup[0]
				tile = tiles[tileKey]
				for gridIndex in range(len(tile.distinctGrids)):
					tile.grid = tile.distinctGrids[gridIndex]
					if board.validMove(tile,r,c):
						if tileGroup not in tileConstraints:
							tileConstraints[tileGroup] = []
						tileConstraints[tileGroup].append((gridIndex,r,c))
						for dr in range(len(tile.grid)):
							for dc in range(len(tile.grid[0])):
								if tile.grid[dr][dc] != ' ':
									boardConstraints[(r+dr,c+dc)].append((tileGroup,gridIndex,r,c))
	return boardConstraints,tileConstraints

def dancingLinks(game):
	"""
	Dancing links is a more creative approach to searching the solution space. The name may be misleading, as the acutal "Dancing Links" algorithm was not implemented here. More over, 
	"Dancing Links" is less of a true algorithm and more of an exploitation of the linked list data structure. This algorithm relies on minimizing the branching factor at each 
	decision point. As such, when a branch is cut, more possibilities can be eliminated at one time. Although the added sophistication requires extra processing between moves, 
	the benefits outweight the costs in this case.

	:param game: the game containing board and tile information
	:type game: Game
	"""
	start_time = time.time()

	game.clearBoard()
	game.solutions = []
	boardConstraints,tileConstraints = createConstraintLists(game)

	dance(game,boardConstraints,tileConstraints)
	game.readyToDrawSolutions = True

	stop_time = time.time()
	print 'Execution time: ' + str(stop_time-start_time)
	print 'Solutions found: ' + str(len(game.solutions))
	print ''

def printTileConstraints(tileConstraints):
	"""
	Used for debugging. Prints the tile constraints dictionary.

	:param tileConstraints: dictionary of tile constraints
	:type tileConstraints: dict
	"""
	print 'Tile Constraints'
	for tileGroup in tileConstraints:
		print '\t' + str(tileGroup) + ': ' + str(tileConstraints[tileGroup])

def printBoardConstraints(boardConstraints):
	"""
	Used for debugging. Prints the board constraints dictionary.

	:param tileConstraints: dictionary of board constraints
	:type tileConstraints: dict
	"""
	print 'Board Constraints'
	for coord in boardConstraints:
		print '\trow %d, col %d:'%coord
		for possibleMove in boardConstraints[coord]:
			print '\t\t' + str(possibleMove)

def doInExternalThread(game, f, a):
	"""
	Spawns a daemon thread to execute the given function if the multithread setting is on; otherwise the main thread is used. The main thread is much faster, but the GUI will freeze during long 
	computations if the main thread is used.

	:param game: the game containing board and tile information
	:type game: Game
	:param f: function to be executed
	:type f: func
	:param a: args for the function
	:type a: tuple
	"""
	if game.multithread.get():
		t = threading.Thread(target = f, args = a)
		t.daemon = True
		t.start()
	else:
		apply(f,a)

def load(game):
	"""
	Loads the currently selected file and updates the display.

	:param game: the game containing board and tile information
	:type game: Game
	"""
	game.load(game.selectedFile.get())
	game.tileInfo = game.tileBucket.export()

def diagnostics(game):
	"""
	Automatically time all puzzle solves under current settings. Dancing Links is used instead of brute force beause otherwise many of the puzzles would not finish.

	:param game: the game containing board and tile information
	:type game: Game
	"""
	for name,path in game.files:
		game.selectedFile.set(name)
		game.loadingOutsideMainThread = True
		game.load(name)
		game.loadingOutsideMainThread = False
		game.tileInfo = game.tileBucket.export()
		print name
		dancingLinks(game)

def main():
	"""
	Initializes the functional section of the user interface and starts TKinter's main graphics loop.
	"""
	settings = {
		'BOARD_WIDTH' : 400,
		'SEPARATOR_WIDTH' : 40,
		'PILE_WIDTH' : 500,
		'TILELIST_WIDTH' : 100,
		'CANVAS_HEIGHT' : 400,
		'BORDER_WIDTH' : 40,
		'GRIDLINE_WIDTH' : 6,
		'SOLN_LIST_HEIGHT' : 100
	}
	game = Game(settings)
	root = game.root

	# Bottom frame
	bottomFrame = game.bottomFrame
	topRow = Frame(bottomFrame)
	bottomRow = Frame(bottomFrame)

	Button(topRow, text='Run Diagnostics', command=lambda:doInExternalThread(game,diagnostics,tuple([game]))).pack(side=LEFT)
	Button(topRow, text='Dancing Links', command=lambda:doInExternalThread(game,dancingLinks,tuple([game]))).pack(side=LEFT)
	Button(topRow, text='Brute Force', command=lambda:doInExternalThread(game,bruteForce,tuple([game]))).pack(side=LEFT)
	Button(topRow, text='Draw Solutions', command=lambda:game.drawSolutions()).pack(side=LEFT)
	Checkbutton(bottomRow, text="Find just one solution", variable=game.findJustOne).pack(side=LEFT)
	Checkbutton(bottomRow, text="Can flip tiles", variable=game.canFlipTiles).pack(side=LEFT)
	Checkbutton(bottomRow, text="Animate", variable=game.animate).pack(side=LEFT)
	Checkbutton(bottomRow, text="Multithread", variable=game.multithread).pack(side=LEFT)
	Button(bottomRow, text='Load', command=lambda:load(game)).pack(side=LEFT)
	apply(OptionMenu, (bottomRow,game.selectedFile) + tuple(f[0] for f in game.files)).pack(side=LEFT)

	topRow.pack(side=TOP)
	bottomRow.pack(side=BOTTOM)

	game.load(game.selectedFile.get())
	game.tileInfo = game.tileBucket.export()

	def update():
		game.update(game.tileInfo)
		game.root.after(35,update)
	game.root.after(0,update)
	
	root.geometry('+0+0')
	root.protocol("WM_DELETE_WINDOW", quit)
	root.mainloop()

if __name__ == '__main__':
	main()
