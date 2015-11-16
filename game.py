#!/usr/bin/python
# from Tkinter import *
from mtTkinter import *
import tkFont
import random

class Board:
	"""
	Represents the board state, including properties of each space in the board and what spaces are occupied.
	"""
	def __init__(self,game,grid):
		"""
		Class constructor.

		:param game: contains display settings
		:type game: Game
		:param grid: grid of board spaces
		:type grid: 2-D array
		"""
		self.rows = len(grid)
		self.cols = len(grid[0])
		borderWidth = game.borderWidth
		gridlineWidth = game.gridlineWidth
		self.grid = grid
		self.occupied = [[grid[r][c] == ' ' for c in range(self.cols)] for r in range(self.rows)]
		self.size = sum([sum([1 for c in range(self.cols) if not self.occupied[r][c]]) for r in range(self.rows)])

		# Logic for uniform square spaces on board and centered board on canvas.
		self.xMargin = self.yMargin = borderWidth
		block_height = (game.canvasHeight-2*borderWidth)/self.rows
		block_width = (game.boardWidth-2*borderWidth)/self.cols
		self.blockSize = min(block_height,block_width)
		if block_height < block_width:
			self.xMargin += ((game.boardWidth-2*borderWidth)-self.blockSize*self.cols)/2
		else:
			self.yMargin += ((game.canvasHeight-2*borderWidth)-self.blockSize*self.rows)/2

		# Check for symmetry
		self.horizontalSymmetry = equivalentGrids(flipHorizontally(grid),grid)
		self.verticalSymmetry = equivalentGrids(flipVertically(grid),grid)
		self.rotationalSymmetry = [equivalentGrids(rotateNTimes(grid,n+1),grid) for n in range(3)]

	def validMove(self,tile,r,c):
		"""
		Determines whether the given tile may be placed on the board at row *r* and col *c*.

		:param tile: tile to check
		:type tile: Tile
		:param r: row at which to check if tile can be placed
		:type r: int
		:param c: col at which to check if tile can be placed
		:type c: int
		"""
		if r < 0 or c < 0: return False
		for row in range(len(tile.grid)):
			for col in range(len(tile.grid[0])):
				if tile.grid[row][col] != ' ':
					if c+col >= len(self.grid[0]) or r+row >= len(self.grid) or self.occupied[r+row][c+col] or self.grid[r+row][c+col] != tile.grid[row][col]:
						return False
		return True
	def placeTile(self,tile,r,c):
		"""
		Places tile and updates the board accordingly.

		:param tile: the tile being placed
		:type tile: Tile
		:param r: row at which to play tile
		:type r: int
		:param c: col at which to play tile
		:type c: int
		"""
		for row in range(len(tile.grid)):
			for col in range(len(tile.grid[0])):
				if tile.grid[row][col] != ' ':
					self.occupied[r+row][c+col] = True
		tile.placeTile(r,c)
	def removeTile(self,tile):
		"""
		Takes tile off of board.

		:param tile: the tile to be removed from the board and despawned
		:type tile: Tile
		"""
		for row in range(len(tile.grid)):
			for col in range(len(tile.grid[0])):
				if tile.grid[row][col] != ' ':
					self.occupied[tile.row+row][tile.col+col] = False
		tile.despawnTile()
	def clear(self):
		"""
		Resets the board so that no spaces are occupied.
		"""
		self.occupied = [[self.grid[r][c] == ' ' for c in range(self.cols)] for r in range(self.rows)]
	def nextEmptySpace(self, startrow, startcol):
		"""
		Returns the next empty spaced, scanning the board top to bottom, left to right.

		:param startrow: the row to start scanning from
		:type startrow: int
		:param startcol: the col to start scanning from
		:type startcol: int
		:returns: (row,col) tuple corresponding to first empty space in the board
		:rtype: tuple(int,int)
		"""
		row = startrow
		col = startcol
		while self.occupied[row][col]:
			col += 1
			if col >= self.cols:
				col = 0
				row += 1
				if row >= self.rows:
					print row
					printGrid(self.occupied)
					return -1,-1
		return row,col

class TileBuilder:
	"""
	Helper class used to create the tiles.
	"""
	def __init__(self,v):
		"""
		Class constructor.

		:param v: the character to be stored in the cell
		:type v: char
		"""
		self.value = v
		self.north = None
		self.east = None
		self.south = None
		self.west = None
		self.grid = [[v]]

class Tile:
	"""
	Represents the tiles in the game.
	"""
	def __init__(self):
		"""
		Class constructor.
		"""
		self.grid = None
		self.spawned = False # Boolean for whether tile should be drawn in pile/board
		self.col = -1 # coordinate of top left element of grid on board; -1 means not on board
		self.row = -1 # coordinate of top left element of grid on board; -1 means not on board
		self.x = -1 # coordinate on canvas; -1 means not on board
		self.y = -1 # coordinate on canvas; -1 means not on board

	def spawnTile(self,game):
		"""
		Takes the tile out of the tile list and moves it to a random spot in the pile (not on the board).

		:param game: the game containing board and tile information
		:type game: Game
		"""
		self.spawned = True
		self.col = -1
		self.row = -1
		self.x = game.boardWidth+game.separatorWidth+game.borderWidth + int(random.random()*(game.pileWidth-2*game.borderWidth-len(self.grid[0])*game.board.blockSize))
		self.y = game.borderWidth + int(random.random()*(game.canvasHeight-2*game.borderWidth-len(self.grid)*game.board.blockSize))
	def despawnTile(self):
		"""
		Returns tile to tile list and resets both board and game coordinates.
		"""
		self.spawned = False
		self.col = -1
		self.row = -1
		self.x = 0
		self.y = 0
	def placeTile(self,r,c):
		"""
		Spawns the tile and updates its board coordinates.

		:param r: row coordinate
		:type r: int
		:param c: row coordinate
		:type c: int
		"""
		self.spawned = True
		self.row = r
		self.col = c
	def drawInList(self,x,y,game,canvas,blockSize):
		"""
		Draws this tile in the tile list. If the tile is spawned, it is drawn in grayscale.

		:param x: describes top-left of block of tile list in which to draw the tile
		:type x: int
		:param y: describes top-left of block of tile list in which to draw the tile
		:type y: int
		:param game: the game containing board and tile information
		:type game: Game
		:param canvas: the canvas on which to draw the tile list
		:type canvas: TKinter.Canvas
		:param blockSize: the desired size of the blocks within the tile list, which is calculated outside the function in order to have uniformity across the tile list
		:type blockSize: int
		"""
		grid = self.grid
		board = game.board

		# Center tile
		width = (game.tilelistWidth-2*game.tilelistBorderWidth)*game.tilelistImageAreaFactor
		x += (width - blockSize*len(grid[0]))/2
		y += (width - blockSize*len(grid))/2

		for row in range(0,len(grid)):
			for col in range(0,len(grid[0])):
				c = grid[row][col]
				if c != ' ':
					x1 = x+col*blockSize
					y1 = y+row*blockSize
					x2 = x1+blockSize
					y2 = y1+blockSize
					canvas.create_rectangle(x1,y1,x2,y2,fill='black',width=game.gridlineWidth,outline='black')
		for row in range(0,len(grid)):
			for col in range(0,len(grid[0])):
				c = grid[row][col]
				if c != ' ':
					color1 = game.tileColors[self.key] if not self.spawned else toGrayScale(game.tileColors[self.key])
					color2 = game.boardColors[c] if not self.spawned else toGrayScale(game.boardColors[c])
					x1 = x+col*blockSize
					y1 = y+row*blockSize
					x2 = x1+blockSize
					y2 = y1+blockSize
					canvas.create_rectangle(x1,y1,x2,y2,fill=color1,width=0)
					canvas.create_rectangle(x1+blockSize*1/5,y1+blockSize*1/5,x2-blockSize*1/5,y2-blockSize*1/5,fill=color2,width=0)

class TileBucket:
	"""
	Container for all tiles.
	"""
	def __init__(self,game,tiles):
		"""
		Class constructor.
		"""
		self.tiles = tiles
		largestTileDim = max([max(len(tiles[x].grid),len(tiles[x].grid[0])) for x in tiles])
		self.blockSize = (game.tilelistWidth-2*game.tilelistBorderWidth)*game.tilelistImageAreaFactor / largestTileDim
	def drawTileList(self,game,canvas):
		"""
		Draws tile list. Spawned tiles are grayed out.

		:param game: contains drawing constants
		:type game: Game
		:param canvas: the canvas on which to draw the tileBucket
		:type canvas: TKinter.Canvas
		"""
		size = game.tilelistWidth
		bw = game.tilelistBorderWidth
		tiles = self.tiles

		canvas.config(scrollregion=(0,0,size,size*len(tiles)+bw-bw*len(tiles)))
		canvas.create_rectangle(0,0,size,size*len(tiles)+bw-bw*len(tiles),fill=game.bgColor,width=0)

		count = 0
		for key in tiles:
			tile = tiles[key]
			bgColor = game.bgColor if not tile.spawned else toGrayScale(game.bgColor)
			canvas.create_rectangle(bw/2,count*size+bw/2-bw*count,size-bw/2,(count+1)*size-bw/2-bw*count,fill=bgColor,width=bw)
			x = bw+(size-2*bw)*(1-game.tilelistImageAreaFactor)/2
			y = bw+(size-2*bw)*(1-game.tilelistImageAreaFactor)/2-bw*count+size*count
			tile.drawInList(x,y,game,canvas,self.blockSize)
			count+=1
	def despawnTiles(self):
		"""
		Despawns all tiles
		"""
		for tileKey in self.tiles:
			self.tiles[tileKey].despawnTile()
	def export(self):
		"""
		Gets the state info for all of the tiles.

		:returns: a dictionary of the state info for the tiles
		:rtype: dict
		"""
		# Export must include tile order and rotation for each tile
		tileInfo = {}
		for key in self.tiles:
			# do not add tiles that are not spawned
			tile = self.tiles[key]
			tileInfo[key] = (tile.row,tile.col,tile.x,tile.y,tile.spawned,tile.distinctGrids.index(tile.grid))
		return tileInfo

class Game:
	"""
	Manager for graphics and board/tile state.
	"""
	def __init__(self,settings={}):
		"""
		Class constructor.

		:param settings: optional parameter containing settings for how the game should be displayed; defaults to {}
		:type settings: dict
		"""
		self.root = Tk()
		self.initializeSettings(settings)
		# root.state('zoomed') # Maximized window
		# root.attributes('-fullscreen', True) # Fullscreen window

		topFrame = Frame(self.root);			topFrame.pack(side=TOP)
		middleFrame = Frame(self.root);			middleFrame.pack()
		solnFrame = Frame(self.root);			solnFrame.pack(fill=X)
		self.bottomFrame = Frame(self.root);	self.bottomFrame.pack(side=BOTTOM)

		# Top frame

		label = Label(topFrame, text='Geometric Puzzle', font=('Helvetica', 20, 'bold'))
		label.pack()

		# Middle frame

		# canvas containing board and pile
		self.canvas1 = Canvas(middleFrame, width=self.canvasWidth, height=self.canvasHeight, bd=0, highlightthickness=0)
		self.canvas1.pack(side=LEFT)

		# canvas containing tile list
		scrollbar = Scrollbar(middleFrame)
		self.canvas2 = Canvas(middleFrame, width = self.tilelistWidth, bd=0, highlightthickness=0)
		self.canvas2.pack(side=LEFT, fill=Y)
		scrollbar.pack(side=LEFT, fill=Y)
		scrollbar.config(command=self.canvas2.yview)
		self.canvas2.config(yscrollcommand=scrollbar.set)

		# canvas containing solutions
		scrollbar2 = Scrollbar(solnFrame, orient = HORIZONTAL)
		self.canvas3 = Canvas(solnFrame, height = self.solnListHeight, bd=0, highlightthickness=0)
		self.canvas3.pack(side=TOP, fill=X)
		scrollbar2.pack(side=BOTTOM, fill=X)
		scrollbar2.config(command=self.canvas3.xview)
		self.canvas3.config(xscrollcommand=scrollbar2.set)

	def initializeSettings(self,settings):
		"""
		Initializes graphics constants and variables. If the settings parameter is empty, then default values are used.
		"""
		self.settings = settings
		self.boardWidth = settings['BOARD_WIDTH'] if 'BOARD_WIDTH' in settings else 300
		self.separatorWidth = settings['SEPARATOR_WIDTH'] if 'SEPARATOR_WIDTH' in settings else 25
		self.pileWidth = settings['PILE_WIDTH'] if 'PILE_WIDTH' in settings else 400
		self.tilelistWidth = settings['TILELIST_WIDTH'] if 'TILELIST_WIDTH' in settings else 100
		self.canvasHeight = settings['CANVAS_HEIGHT'] if 'CANVAS_HEIGHT' in settings else 300
		self.canvasWidth = settings['CANVAS_WIDTH'] if 'CANVAS_WIDTH' in settings else (self.boardWidth + self.separatorWidth + self.pileWidth)
		self.borderWidth = settings['BORDER_WIDTH'] if 'BORDER_WIDTH' in settings else 40
		self.gridlineWidth = settings['GRIDLINE_WIDTH'] if 'GRIDLINE_WIDTH' in settings else 6
		self.tilelistBorderWidth = settings['TILELIST_BORDER_WIDTH'] if 'TILELIST_BORDER_WIDTH' in settings else 6
		self.tilelistImageAreaFactor = settings['TILELIST_IMAGE_AREA_FACTOR'] if 'TILELIST_IMAGE_AREA_FACTOR' in settings else 0.8
		self.solnListHeight = settings['SOLN_LIST_HEIGHT'] if 'SOLN_LIST_HEIGHT' in settings else 100
		self.maxSolnsDrawn = settings['MAX_SOLNS_DRAWN'] if 'MAX_SOLNS_DRAWN' in settings else 36
		self.bgColor = settings['BG_COLOR'] if 'BG_COLOR' in settings else '#007fff'
		self.puzzleDirectory = settings['PUZZLE_DIRECTORY'] if 'PUZZLE_DIRECTORY' in settings else '/puzzles'
		self.boardColors = {' ':'#000000'}
		self.tileColors = {}

		import os, inspect
		self.files = []
		count = 1
		for f in os.listdir(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))+self.puzzleDirectory):
			if f.endswith('.txt'):
				self.files.append(('Puzzle ' + str(count) + ': ' + f.replace('.txt',''), self.puzzleDirectory[1:] + '/' + f))
				count+=1

		self.findJustOne = IntVar(master=self.root, value=True)
		self.canFlipTiles = IntVar(master=self.root, value=True)
		self.animate = IntVar(master=self.root, value=True)
		self.multithread = IntVar(master=self.root, value=True)
		self.selectedFile = StringVar(master=self.root, value=self.files[0][0])
		self.readyToDrawSolutions = False
		self.loadingOutsideMainThread = False
	def load(self,fileKey):
		"""
		Loads the currently selected puzzle. In the event that a bad board config file is given, the user is notified via the console.

		:param filekey: refers to the file containing the puzzle to be loaded
		:type filekey: str
		"""
		validBoard = self.parseInputFile(fileKey)
		self.drawBoardAndTiles()
		self.tileBucket.drawTileList(self,self.canvas2)
		self.solutions = []
		self.canvas3.delete('all')
		self.canvas3.config(scrollregion=(0,0,0,0))
		if not validBoard:
			self.canvas3.create_text(self.root.winfo_width()/2,self.solnListHeight/2,text='Invalid board! Not enough tiles.',font=tkFont.Font(size=30,weight='bold'))
	def update(self,tileInfo = None):
		"""
		Redraws the board, tiles, and tile list.

		:param tileInfo: if provided, used to determine tile states; otherwise, self.tileBucket is used
		:type tileInfo: dict
		"""
		if self.loadingOutsideMainThread:
			return
		self.canvas1.delete("all")
		self.canvas2.delete("all")
		tileBucket = None
		if tileInfo is None:
			tileBucket = self.tileBucket
		if tileInfo is not None:
			tiles = {}
			for key in tileInfo:
				tile = Tile()
				tile.row,tile.col,tile.x,tile.y,tile.spawned,rotationIndex = tileInfo[key]
				tile.grid = self.tileBucket.tiles[key].distinctGrids[rotationIndex]
				tile.key = key
				tiles[key] = tile
			tileBucket = TileBucket(self,tiles)
		self.drawBoardAndTiles(tileBucket)
		tileBucket.drawTileList(self,self.canvas2)
		if self.readyToDrawSolutions:
			self.readyToDrawSolutions = False
			self.drawSolutions()
	def drawBoardAndTiles(self,tileBucket = None):
		"""
		Draws both the board and the tiles have been placed on the board.

		:param tileBucket: used to determine if and where tiles should be drawn on the board
		:type tileBucket: TileBucket
		"""
		# Draw border
		self.canvas1.create_rectangle(0,0,self.canvasWidth,self.canvasHeight,fill=self.bgColor,width=0)
		self.canvas1.create_rectangle(self.boardWidth,0,self.boardWidth+self.separatorWidth,self.canvasHeight,fill='#000000',width=0)

		if tileBucket is None:
			tileBucket = self.tileBucket
			
		self.drawBoard()

		for key in tileBucket.tiles:
			tile = tileBucket.tiles[key]
			if tile.spawned:
				if tile.col != -1 and tile.row != -1:
					self.drawTileOnBoard(tile)
				else:
					self.drawTileOnCanvas(tile)
	def drawTileOnCanvas(self,tile):
		"""
		Draws a tile that has been spawned, but not placed on the board, based on the tile.x and tile.y.

		:param tile: the tile to be drawn
		:type tile: Tile
		"""
		w = self.gridlineWidth
		bw = self.tilelistBorderWidth
		grid = tile.grid
		canvas = self.canvas1
		board = self.board

		global boardColors
		for row in range(0,len(grid)):
			for col in range(0,len(grid[0])):
				c = grid[row][col]
				if c != ' ':
					x1 = tile.x+col*board.blockSize
					y1 = tile.y+row*board.blockSize
					x2 = x1+board.blockSize
					y2 = y1+board.blockSize
					canvas.create_rectangle(x1,y1,x2,y2,fill='black',width=w,outline='black')
		for row in range(0,len(grid)):
			for col in range(0,len(grid[0])):
				c = grid[row][col]
				if c != ' ':
					x1 = tile.x+col*board.blockSize
					y1 = tile.y+row*board.blockSize
					x2 = x1+board.blockSize
					y2 = y1+board.blockSize
					canvas.create_rectangle(x1,y1,x2,y2,fill=self.tileColors[tile.key],width=0)
					canvas.create_rectangle(x1+board.blockSize*1/5,y1+board.blockSize*1/5,x2-board.blockSize*1/5,y2-board.blockSize*1/5,fill=self.boardColors[c],width=0)
	def drawTileOnBoard(self,tile):
		"""
		Draws a tile that has been both spawned and placed on the board based on its tile.row and tile.col.

		:param tile: the tile to be drawn
		:type tile: Tile
		"""
		board = self.board
		canvas = self.canvas1
		grid = tile.grid
		for row in range(0,len(grid)):
			for col in range(0,len(grid[0])):
				c = grid[row][col]
				if c != ' ':
					x1 = board.xMargin+tile.col*board.blockSize+col*board.blockSize
					y1 = board.yMargin+tile.row*board.blockSize+row*board.blockSize
					x2 = x1+board.blockSize
					y2 = y1+board.blockSize
					canvas.create_rectangle(x1,y1,x2,y2,fill='black',width=self.gridlineWidth,outline='black')
		for row in range(0,len(grid)):
			for col in range(0,len(grid[0])):
				c = grid[row][col]
				if c != ' ':
					x1 = board.xMargin+tile.col*board.blockSize+col*board.blockSize
					y1 = board.yMargin+tile.row*board.blockSize+row*board.blockSize
					x2 = x1+board.blockSize
					y2 = y1+board.blockSize
					canvas.create_rectangle(x1,y1,x2,y2,fill=self.tileColors[tile.key],width=0)
					canvas.create_rectangle(x1+board.blockSize*1/5,y1+board.blockSize*1/5,x2-board.blockSize*1/5,y2-board.blockSize*1/5,fill=self.boardColors[c],width=0)
	def drawSolutions(self):
		"""
		Draws solutions that have been found and added to the solutions list.
		"""
		self.canvas3.delete("all")

		size = self.solnListHeight
		bw = self.tilelistBorderWidth
		canvas = self.canvas3
		board = self.board
		solns = self.solutions

		if len(solns) == 0:
			canvas.create_text(self.root.winfo_width()/2,size/2,text='No solutions!',font=tkFont.Font(size=30,weight='bold'))

		canvas.config(scrollregion=(0,0,size*len(solns)+bw-bw*len(solns),size))

		count = 0
		for tileInfo in solns:
			bgColor = self.bgColor
			canvas.create_rectangle(count*size+bw/2-bw*count,bw/2,(count+1)*size-bw/2-bw*count,size-bw/2,fill=bgColor,width=bw)
			x = bw+(size-2*bw)*(1-self.tilelistImageAreaFactor)/2-bw*count+size*count
			y = bw+(size-2*bw)*(1-self.tilelistImageAreaFactor)/2

			# draw board
			blockSize = (size-2*bw)*(self.tilelistImageAreaFactor)/max(len(board.grid),len(board.grid[0]))
			# center grids
			x += ((size-2*bw)*(self.tilelistImageAreaFactor) - blockSize*len(board.grid[0]))/2
			y += ((size-2*bw)*(self.tilelistImageAreaFactor) - blockSize*len(board.grid))/2
			# board background
			canvas.create_rectangle(x,y,x+blockSize*len(board.grid[0]),y+blockSize*len(board.grid),fill='black',width=3,outline='black')
			
			# draw tiles
			tiles = {}
			for key in tileInfo:
				tile = Tile()
				tile.row,tile.col,tile.x,tile.y,tile.spawned,rotationIndex = tileInfo[key]
				tile.grid = self.tileBucket.tiles[key].distinctGrids[rotationIndex]
				tiles[key] = tile
			for key in tiles:
				tile = tiles[key]
				if tile.row == -1 or tile.col == -1:
					continue
				grid = tile.grid
				for row in range(0,len(grid)):
					for col in range(0,len(grid[0])):
						c = grid[row][col]
						if c != ' ':
							x1 = x+tile.col*blockSize+col*blockSize
							y1 = y+tile.row*blockSize+row*blockSize
							x2 = x1+blockSize
							y2 = y1+blockSize
							canvas.create_rectangle(x1,y1,x2,y2,fill='black',width=2,outline='black')
				for row in range(0,len(grid)):
					for col in range(0,len(grid[0])):
						c = grid[row][col]
						if c != ' ':
							x1 = x+tile.col*blockSize+col*blockSize
							y1 = y+tile.row*blockSize+row*blockSize
							x2 = x1+blockSize
							y2 = y1+blockSize
							canvas.create_rectangle(x1,y1,x2,y2,fill=self.tileColors[key],width=0)
			count+=1
	def drawBoard(self):
		"""
		Draws the board.
		"""
		canvas = self.canvas1
		board = self.board
		grid = board.grid
		for row in range(0,len(grid)):
			for col in range(0,len(grid[0])):
				c = grid[row][col]
				x1 = board.xMargin+col*board.blockSize
				y1 = board.yMargin+row*board.blockSize
				x2 = x1+board.blockSize
				y2 = y1+board.blockSize
				canvas.create_rectangle(x1,y1,x2,y2,fill=self.boardColors[c],width=self.gridlineWidth,outline='black')
	def clearBoard(self):
		"""
		Resets board and despawns all tiles.
		"""
		self.board.clear()
		self.tileBucket.despawnTiles()
	def parseInputFile(self, filekey):
		"""
		Interprets the board configurations in the text file referred to by the fileKey. Each body of text is taken to be a tile where the largest tile is the board.

		:param filekey: refers to the file containing the puzzle to be read and loaded
		:type filekey: str
		:returns: True if the board config file was valid; False otherwise
		:rtype: bool:
		"""
		self.boardColors = {' ':"#000000"}
		self.tileColors = {}
		tiles = {}
		
		filepath = dict(self.files)[filekey]
		f = open(filepath,'r')

		inputGrid = [[c for c in line[0:len(line)-1]] for line in f]
		
		largestTileId = -1
		largestTileSize = -1
		count = 0
		for i in range(len(inputGrid)):
			for j in range(len(inputGrid[i])):
				c = inputGrid[i][j]
				if c != ' ':
					if c not in self.boardColors:
						self.boardColors[c] = randomColor()
					tiles[count],size = buildTile(inputGrid,i,j)
					if (largestTileSize == -1 or size > largestTileSize):
						largestTileId = count
						largestTileSize = size
					count+=1

		boardGrid = gridFromTile(tiles[largestTileId])
		self.board = Board(self,boardGrid)
		del tiles[largestTileId]

		for key in tiles:
			tile = Tile()
			tile.grid = gridFromTile(tiles[key])
			tile.size = sum([sum([1 for ch in tile.grid[r] if ch != ' ']) for r in range(len(tile.grid))])
			tile.key = key
			self.tileColors[key] = randomColor()
			
			grid = tile.grid
			distinctGrids = []
			for n in range(4):
				temp = [[grid[y][x] for x in range(len(grid[0]))] for y in range(len(grid))]
				if temp not in distinctGrids:
					distinctGrids.append(temp)
				grid = rotateClockwise(grid)
			if self.canFlipTiles.get():
				grid = flipHorizontally(grid)
				for n in range(4):
					temp = [[grid[y][x] for x in range(len(grid[0]))] for y in range(len(grid))]
					if temp not in distinctGrids:
						distinctGrids.append(temp)
					grid = rotateClockwise(grid)
				grid = flipHorizontally(grid)
			tile.distinctGrids = distinctGrids
			tiles[key] = tile

		self.tileBucket = TileBucket(self,tiles)
		self.tileBucket.tileGroups = groupTiles(tiles)
		self.tileBucket.size = sum([tiles[key].size for key in tiles])

		for tileGroup in self.tileBucket.tileGroups:
			mainTile = None
			for tileKey in tileGroup:
				if mainTile is None:
					mainTile = self.tileBucket.tiles[tileKey]
				else:
					self.tileBucket.tiles[tileKey].distinctGrids = mainTile.distinctGrids

		# validate board
		if self.tileBucket.size < self.board.size:
			return False
		return True

def printGrid(grid):
	"""
	Prints grid.

	:param grid: grid to be printed
	:type grid: 2-D array
	"""
	for l in grid:
		print l
	print
def printTile(tile):
	"""
	Prints tile.

	:param tile: tile to be printed
	:type tile: Tile
	"""
	printGrid(tile.grid)
def gridFromTile(tile):
	"""
	Extracts grid from given tile builder.

	:param tile: tile to extract grid from
	:type tile: TileBuilder
	:returns: grid represented by given tile
	:rtype: 2-D array
	"""
	# Tile points intitially to furthest left item in top
	# row based on parsing strategy used to read file.
	min_i = 0
	max_i = 0
	min_j = 0
	max_j = 0
	points = []
	visited = {tile:None}
	tileStack = [(tile,0,0)]

	while len(tileStack) > 0:
		t,i,j = tileStack.pop()
		points.append((t.value,i,j))

		if t.north is not None and t.north not in visited:
			tileStack.append((t.north,i-1,j))
			min_i = min(min_i,i-1)
		if t.south is not None and t.south not in visited:
			tileStack.append((t.south,i+1,j))
			max_i = max(max_i,i+1)
		if t.west is not None and t.west not in visited:
			tileStack.append((t.west,i,j-1))
			min_j = min(min_j,j-1)
		if t.east is not None and t.east not in visited:
			tileStack.append((t.east,i,j+1))
			max_j = max(max_j,j+1)

		visited[t] = None

	grid = [[' ' for j in range(max_j-min_j+1)] for i in range(max_i-min_i+1)]
	for v,i,j in points:
		grid[i-min_i][j-min_j] = v

	return grid
def buildTile(grid,i,j,size=0):
	"""
	Creates a tile builder describing the shape of the tile. Starts at the i-th row and j-th col and consumes every tile square within 1 space.

	:param grid: the array of the file being loaded
	:type grid: 2-D array
	:param i: row to start building from
	:type i: int
	:param j: col to start building from
	:type j: int
	:returns: tile builder and tile size
	:rtype: TileBuilder and int
	"""
	tile = TileBuilder(grid[i][j])
	grid[i][j] = ' '
	size += 1

	# North
	if i>0 and j<len(grid[i-1]) and grid[i-1][j] != ' ':
		tile.north,size = buildTile(grid,i-1,j,size)
	# South
	if i+1<len(grid) and j<len(grid[i+1]) and grid[i+1][j] != ' ':
		tile.south,size = buildTile(grid,i+1,j,size)
	# West
	if j>0 and grid[i][j-1] != ' ':
		tile.west,size = buildTile(grid,i,j-1,size)
	# East
	if j+1<len(grid[i]) and grid[i][j+1] != ' ':
		tile.east,size = buildTile(grid,i,j+1,size)

	return tile,size
def randomColor():
	"""
	Gives a random color.

	:returns: a random color
	:rtype: color formatted as '#RRGGBB'
	"""
	hexDigits = ['0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f']
	return '#'+''.join([random.choice(hexDigits) for x in range(6)])
def toGrayScale(rgb):
	"""
	Converts rgb to grayscale. Red, green, and blue are weighted according to cognitive research into how human vision weights each of the basic colors.

	:param rgb: color to be converted to grayscale, formatted as '#RRGGBB'
	:type rgb: str
	:returns: grayscale color
	:rtype: color formatted as '#RRGGBB'
	"""
	r = int(rgb[1:3],16)
	g = int(rgb[3:5],16)
	b = int(rgb[6:8],16)
	gray = int(0.299*r+0.587*g+0.114*b)
	grayHex = '{:02x}'.format(gray)
	return '#'+grayHex+grayHex+grayHex

def groupTiles(tiles):
	"""
	Groups together non-distinct tiles.

	:param tiles: the dict containing the all tiles on the board
	"""
	groups = {}
	for tileKey1 in tiles:
		group = []
		for tileKey2 in tiles:
			if tiles[tileKey1].grid in tiles[tileKey2].distinctGrids:
				group.append(tileKey2)
		groups[min(group)] = group
	return [tuple(groups[g]) for g in groups]

def copyGrid(grid):
	"""
	Creates a copy of grid in a new array so that future modifications do not affect the old grid.

	:param grid: the array that is being copied
	:type grid: 2-D array
	:returns: a deepcopy of grid
	:rtype: 2-D array
	"""
	return [[cell for cell in row] for row in grid]
def flipHorizontally(grid):
	"""
	Creates a copy of grid that is reflected across the y-axis.

	:param grid: the array that is being flipped
	:type grid: 2-D array
	:returns: a horizontally flipped version of grid
	:rtype: 2-D array
	"""
	g = copyGrid(grid)
	g = [[c for c in reversed(row)] for row in g]
	return g
def flipVertically(grid):
	"""
	Creates a copy of grid that is reflected across the x-axis.

	:param grid: the array that is being flipped
	:type grid: 2-D array
	:returns: a vertically flipped version of grid
	:rtype: 2-D array
	"""
	g = transpose(flipHorizontally(transpose(copyGrid(grid))))
	return g
def transpose(grid):
	"""
	Creates a transposed copy of grid.

	:param grid: the array that is being transposed
	:type grid: 2-D array
	:returns: a version of grid that has had the rows and columns swapped
	:rtype: 2-D array
	"""
	g = [[c for c in row] for row in zip(*copyGrid(grid))]
	return g
def rotateClockwise(grid): # transpose and flip
	"""
	Creates a clockwise-rotated copy of grid. This is accomplished by noting the fact that a clockwise rotation can be accomplished with a transpose followed by a horizontal flip.

	:param grid: the array that is being rotated
	:type grid: 2-D array
	:returns: a version of grid that has been rotated clockwise
	:rtype: 2-D array
	"""
	g = transpose(copyGrid(grid))
	g = flipHorizontally(g)
	return g
def rotateNTimes(grid,n):
	"""
	Creates a copy of grid that has been rotated clockwise N times.

	:param grid: the array that is being transposed
	:type grid: 2-D array
	:param n: the number of times to rotate the grid
	:type n: int
	:returns: a version of grid that has had the rows and columns swapped
	:rtype: 2-D array
	"""
	g = copyGrid(grid)
	for i in range(n):
		g = rotateClockwise(g)
	return g
def equivalentGrids(grid1,grid2):
	"""
	Determines whether grid1 and grid2 share equality in all cells.

	:param grid1: the array that is being transposed
	:type grid1: 2-D array
	:param grid2: the array that is being transposed
	:type grid2: 2-D array
	:returns: whether or not the given grids are equivalent
	:rtype: bool
	"""
	if len(grid1) != len(grid2) or len(grid1[0]) != len(grid2[0]):
		return False
	for r in range(len(grid1)):
		for c in range(len(grid1[0])):
			if grid1[r][c] != grid2[r][c]:
				return False
	return True