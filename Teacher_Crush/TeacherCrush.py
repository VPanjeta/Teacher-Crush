import random, time, pygame, sys, copy
from pygame.locals import *

FPS = 30 # frames per second to update the screen
WINDOWWIDTH = 1000  # width of the program's window, in pixels
WINDOWHEIGHT = 1000 # height in pixels

BOARDWIDTH = 6 # how many columns in the board
BOARDHEIGHT = 6 # how many rows in the board
TEACHERIMAGESIZE = 128 # width & height of each space in pixels

# NUMTEACHERIMAGES is the number of TEACHER types. You will need .png image
# files named TEACHER0.png, TEACHER1.png, etc. up to TEACHER(N-1).png.
NUMTEACHERIMAGES = 7
assert NUMTEACHERIMAGES >= 5 # game needs at least 5 types of TEACHERs to work

# NUMMATCHSOUNDS is the number of different sounds to choose from when
# a match is made. The .wav files are named match0.wav, match1.wav, etc.
NUMMATCHSOUNDS = 6

MOVERATE = 25 # 1 to 100, larger num means faster animations
DEDUCTSPEED = 0.8 # reduces score by 1 point every DEDUCTSPEED seconds.

#             R    G    B
PURPLE    = (255,   0, 255)
LIGHTBLUE = (170, 190, 255)
BLUE      = (  0,   0, 255)
RED       = (255, 100, 100)
BLACK     = (  0,   0,   0)
BROWN     = ( 85,  65,   0)
HIGHLIGHTCOLOR = PURPLE # color of the selected TEACHER's border
BGCOLOR = LIGHTBLUE # background color on the screen
GRIDCOLOR = BLUE # color of the game board
GAMEOVERCOLOR = RED # color of the "Game over" text.
GAMEOVERBGCOLOR = BLACK # background color of the "Game over" text.
SCORECOLOR = BROWN # color of the text for the player's score

# The amount of space to the sides of the board to the edge of the window
# is used several times, so calculate it once here and store in variables.
XMARGIN = int((WINDOWWIDTH - TEACHERIMAGESIZE * BOARDWIDTH) / 2)
YMARGIN = int((WINDOWHEIGHT - TEACHERIMAGESIZE * BOARDHEIGHT) / 2)

# constants for direction values
UP = 'up'
DOWN = 'down'
LEFT = 'left'
RIGHT = 'right'

EMPTY_SPACE = -1 # an arbitrary, nonpositive value
ROWABOVEBOARD = 'row above board' # an arbitrary, noninteger value

def main():
    global FPSCLOCK, DISPLAYSURF, TEACHERIMAGES, GAMESOUNDS, BASICFONT, BOARDRECTS

    # Initial set up.
    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
    pygame.display.set_caption('TeacherGem')
    BASICFONT = pygame.font.Font('freesansbold.ttf', 36)

    # Load the images
    TEACHERIMAGES = []
    for i in range(1, NUMTEACHERIMAGES+1):
        TEACHERImage = pygame.image.load('TEACHER%s.png' % i)
        if TEACHERImage.get_size() != (TEACHERIMAGESIZE, TEACHERIMAGESIZE):
            TEACHERImage = pygame.transform.smoothscale(TEACHERImage, (TEACHERIMAGESIZE, TEACHERIMAGESIZE))
        TEACHERIMAGES.append(TEACHERImage)

    # Load the sounds.
    GAMESOUNDS = {}
    GAMESOUNDS['bad swap'] = pygame.mixer.Sound('badswap.wav')
    GAMESOUNDS['match'] = []
    for i in range(NUMMATCHSOUNDS):
        GAMESOUNDS['match'].append(pygame.mixer.Sound('match%s.wav' % i))

    # Create pygame.Rect objects for each board space to
    # do board-coordinate-to-pixel-coordinate conversions.
    BOARDRECTS = []
    for x in range(BOARDWIDTH):
        BOARDRECTS.append([])
        for y in range(BOARDHEIGHT):
            r = pygame.Rect((XMARGIN + (x * TEACHERIMAGESIZE),
                             YMARGIN + (y * TEACHERIMAGESIZE),
                             TEACHERIMAGESIZE,
                             TEACHERIMAGESIZE))
            BOARDRECTS[x].append(r)

    while True:
        runGame()


def runGame():
    # Plays through a single game. When the game is over, this function returns.

    # initalize the board
    gameBoard = getBlankBoard()
    score = 0
    fillBoardAndAnimate(gameBoard, [], score) # Drop the initial TEACHERs.

    # initialize variables for the start of a new game
    firstSelectedTEACHER = None
    lastMouseDownX = None
    lastMouseDownY = None
    gameIsOver = False
    lastScoreDeduction = time.time()
    clickContinueTextSurf = None

    while True: # main game loop
        clickedSpace = None
        for event in pygame.event.get(): # event handling loop
            if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            elif event.type == KEYUP and event.key == K_BACKSPACE:
                return # start a new game

            elif event.type == MOUSEBUTTONUP:
                if gameIsOver:
                    return # after games ends, click to start a new game

                if event.pos == (lastMouseDownX, lastMouseDownY):
                    # This event is a mouse click, not the end of a mouse drag.
                    clickedSpace = checkForTEACHERClick(event.pos)
                else:
                    # this is the end of a mouse drag
                    firstSelectedTEACHER = checkForTEACHERClick((lastMouseDownX, lastMouseDownY))
                    clickedSpace = checkForTEACHERClick(event.pos)
                    if not firstSelectedTEACHER or not clickedSpace:
                        # if not part of a valid drag, deselect both
                        firstSelectedTEACHER = None
                        clickedSpace = None
            elif event.type == MOUSEBUTTONDOWN:
                # this is the start of a mouse click or mouse drag
                lastMouseDownX, lastMouseDownY = event.pos

        if clickedSpace and not firstSelectedTEACHER:
            # This was the first TEACHER clicked on.
            firstSelectedTEACHER = clickedSpace
        elif clickedSpace and firstSelectedTEACHER:
            # Two TEACHERs have been clicked on and selected. Swap the TEACHERs.
            firstSwappingTEACHER, secondSwappingTEACHER = getSwappingTEACHERs(gameBoard, firstSelectedTEACHER, clickedSpace)
            if firstSwappingTEACHER == None and secondSwappingTEACHER == None:
                # If both are None, then the TEACHERs were not adjacent
                firstSelectedTEACHER = None # deselect the first TEACHER
                continue

            # Show the swap animation on the screen.
            boardCopy = getBoardCopyMinusTEACHERs(gameBoard, (firstSwappingTEACHER, secondSwappingTEACHER))
            animateMovingTEACHERs(boardCopy, [firstSwappingTEACHER, secondSwappingTEACHER], [], score)

            # Swap the TEACHERs in the board data structure.
            gameBoard[firstSwappingTEACHER['x']][firstSwappingTEACHER['y']] = secondSwappingTEACHER['imageNum']
            gameBoard[secondSwappingTEACHER['x']][secondSwappingTEACHER['y']] = firstSwappingTEACHER['imageNum']

            # See if this is a matching move.
            matchedTEACHERs = findMatchingTEACHERs(gameBoard)
            if matchedTEACHERs == []:
                # Was not a matching move; swap the TEACHERs back
                GAMESOUNDS['bad swap'].play()
                animateMovingTEACHERs(boardCopy, [firstSwappingTEACHER, secondSwappingTEACHER], [], score)
                gameBoard[firstSwappingTEACHER['x']][firstSwappingTEACHER['y']] = firstSwappingTEACHER['imageNum']
                gameBoard[secondSwappingTEACHER['x']][secondSwappingTEACHER['y']] = secondSwappingTEACHER['imageNum']
            else:
                # This was a matching move.
                scoreAdd = 0
                while matchedTEACHERs != []:
                    # Remove matched TEACHERs, then pull down the board.

                    # points is a list of dicts that tells fillBoardAndAnimate()
                    # where on the screen to display text to show how many
                    # points the player got. points is a list because if
                    # the playergets multiple matches, then multiple points text should appear.
                    points = []
                    for TEACHERSet in matchedTEACHERs:
                        scoreAdd += (10 + (len(TEACHERSet) - 3) * 10)
                        for TEACHER in TEACHERSet:
                            gameBoard[TEACHER[0]][TEACHER[1]] = EMPTY_SPACE
                        points.append({'points': scoreAdd,
                                       'x': TEACHER[0] * TEACHERIMAGESIZE + XMARGIN,
                                       'y': TEACHER[1] * TEACHERIMAGESIZE + YMARGIN})
                    random.choice(GAMESOUNDS['match']).play()
                    score += scoreAdd

                    # Drop the new TEACHERs.
                    fillBoardAndAnimate(gameBoard, points, score)

                    # Check if there are any new matches.
                    matchedTEACHERs = findMatchingTEACHERs(gameBoard)
            firstSelectedTEACHER = None

            if not canMakeMove(gameBoard):
                gameIsOver = True

        # Draw the board.
        DISPLAYSURF.fill(BGCOLOR)
        drawBoard(gameBoard)
        if firstSelectedTEACHER != None:
            highlightSpace(firstSelectedTEACHER['x'], firstSelectedTEACHER['y'])
        if gameIsOver:
            if clickContinueTextSurf == None:
                # Only render the text once. In future iterations, just
                # use the Surface object already in clickContinueTextSurf
                clickContinueTextSurf = BASICFONT.render('Final Score: %s (Click to continue)' % (score), 1, GAMEOVERCOLOR, GAMEOVERBGCOLOR)
                clickContinueTextRect = clickContinueTextSurf.get_rect()
                clickContinueTextRect.center = int(WINDOWWIDTH / 2), int(WINDOWHEIGHT / 2)
            DISPLAYSURF.blit(clickContinueTextSurf, clickContinueTextRect)
        elif score > 0 and time.time() - lastScoreDeduction > DEDUCTSPEED:
            # score drops over time
            score -= 1
            lastScoreDeduction = time.time()
        drawScore(score)
        pygame.display.update()
        FPSCLOCK.tick(FPS)


def getSwappingTEACHERs(board, firstXY, secondXY):
    # If the TEACHERs at the (X, Y) coordinates of the two TEACHERs are adjacent,
    # then their 'direction' keys are set to the appropriate direction
    # value to be swapped with each other.
    # Otherwise, (None, None) is returned.
    firstTEACHER = {'imageNum': board[firstXY['x']][firstXY['y']],
                'x': firstXY['x'],
                'y': firstXY['y']}
    secondTEACHER = {'imageNum': board[secondXY['x']][secondXY['y']],
                 'x': secondXY['x'],
                 'y': secondXY['y']}
    highlightedTEACHER = None
    if firstTEACHER['x'] == secondTEACHER['x'] + 1 and firstTEACHER['y'] == secondTEACHER['y']:
        firstTEACHER['direction'] = LEFT
        secondTEACHER['direction'] = RIGHT
    elif firstTEACHER['x'] == secondTEACHER['x'] - 1 and firstTEACHER['y'] == secondTEACHER['y']:
        firstTEACHER['direction'] = RIGHT
        secondTEACHER['direction'] = LEFT
    elif firstTEACHER['y'] == secondTEACHER['y'] + 1 and firstTEACHER['x'] == secondTEACHER['x']:
        firstTEACHER['direction'] = UP
        secondTEACHER['direction'] = DOWN
    elif firstTEACHER['y'] == secondTEACHER['y'] - 1 and firstTEACHER['x'] == secondTEACHER['x']:
        firstTEACHER['direction'] = DOWN
        secondTEACHER['direction'] = UP
    else:
        # These TEACHERs are not adjacent and can't be swapped.
        return None, None
    return firstTEACHER, secondTEACHER


def getBlankBoard():
    # Create and return a blank board data structure.
    board = []
    for x in range(BOARDWIDTH):
        board.append([EMPTY_SPACE] * BOARDHEIGHT)
    return board


def canMakeMove(board):
    # Return True if the board is in a state where a matching
    # move can be made on it. Otherwise return False.

    # The patterns in oneOffPatterns represent TEACHERs that are configured
    # in a way where it only takes one move to make a triplet.
    oneOffPatterns = (((0,1), (1,0), (2,0)),
                      ((0,1), (1,1), (2,0)),
                      ((0,0), (1,1), (2,0)),
                      ((0,1), (1,0), (2,1)),
                      ((0,0), (1,0), (2,1)),
                      ((0,0), (1,1), (2,1)),
                      ((0,0), (0,2), (0,3)),
                      ((0,0), (0,1), (0,3)))

    # The x and y variables iterate over each space on the board.
    # If we use + to represent the currently iterated space on the
    # board, then this pattern: ((0,1), (1,0), (2,0))refers to identical
    # TEACHERs being set up like this:
    #
    #     +A
    #     B
    #     C
    #
    # That is, TEACHER A is offset from the + by (0,1), TEACHER B is offset
    # by (1,0), and TEACHER C is offset by (2,0). In this case, TEACHER A can
    # be swapped to the left to form a vertical three-in-a-row triplet.
    #
    # There are eight possible ways for the TEACHERs to be one move
    # away from forming a triple, hence oneOffPattern has 8 patterns.

    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
            for pat in oneOffPatterns:
                # check each possible pattern of "match in next move" to
                # see if a possible move can be made.
                if (getTEACHERAt(board, x+pat[0][0], y+pat[0][1]) == \
                    getTEACHERAt(board, x+pat[1][0], y+pat[1][1]) == \
                    getTEACHERAt(board, x+pat[2][0], y+pat[2][1]) != None) or \
                   (getTEACHERAt(board, x+pat[0][1], y+pat[0][0]) == \
                    getTEACHERAt(board, x+pat[1][1], y+pat[1][0]) == \
                    getTEACHERAt(board, x+pat[2][1], y+pat[2][0]) != None):
                    print(x,y,pat)
                    return True # return True the first time you find a pattern
    return False


def drawMovingTEACHER(TEACHER, progress):
    # Draw a TEACHER sliding in the direction that its 'direction' key
    # indicates. The progress parameter is a number from 0 (just
    # starting) to 100 (slide complete).
    movex = 0
    movey = 0
    progress *= 0.01

    if TEACHER['direction'] == UP:
        movey = -int(progress * TEACHERIMAGESIZE)
    elif TEACHER['direction'] == DOWN:
        movey = int(progress * TEACHERIMAGESIZE)
    elif TEACHER['direction'] == RIGHT:
        movex = int(progress * TEACHERIMAGESIZE)
    elif TEACHER['direction'] == LEFT:
        movex = -int(progress * TEACHERIMAGESIZE)

    basex = TEACHER['x']
    basey = TEACHER['y']
    if basey == ROWABOVEBOARD:
        basey = -1

    pixelx = XMARGIN + (basex * TEACHERIMAGESIZE)
    pixely = YMARGIN + (basey * TEACHERIMAGESIZE)
    r = pygame.Rect( (pixelx + movex, pixely + movey, TEACHERIMAGESIZE, TEACHERIMAGESIZE) )
    DISPLAYSURF.blit(TEACHERIMAGES[TEACHER['imageNum']], r)


def pullDownAllTEACHERs(board):
    # pulls down TEACHERs on the board to the bottom to fill in any gaps
    for x in range(BOARDWIDTH):
        TEACHERsInColumn = []
        for y in range(BOARDHEIGHT):
            if board[x][y] != EMPTY_SPACE:
                TEACHERsInColumn.append(board[x][y])
        board[x] = ([EMPTY_SPACE] * (BOARDHEIGHT - len(TEACHERsInColumn))) + TEACHERsInColumn


def getTEACHERAt(board, x, y):
    if x < 0 or y < 0 or x >= BOARDWIDTH or y >= BOARDHEIGHT:
        return None
    else:
        return board[x][y]


def getDropSlots(board):
    # Creates a "drop slot" for each column and fills the slot with a
    # number of TEACHERs that that column is lacking. This function assumes
    # that the TEACHERs have been gravity dropped already.
    boardCopy = copy.deepcopy(board)
    pullDownAllTEACHERs(boardCopy)

    dropSlots = []
    for i in range(BOARDWIDTH):
        dropSlots.append([])

    # count the number of empty spaces in each column on the board
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT-1, -1, -1): # start from bottom, going up
            if boardCopy[x][y] == EMPTY_SPACE:
                possibleTEACHERs = list(range(len(TEACHERIMAGES)))
                for offsetX, offsetY in ((0, -1), (1, 0), (0, 1), (-1, 0)):
                    # Narrow down the possible TEACHERs we should put in the
                    # blank space so we don't end up putting an two of
                    # the same TEACHERs next to each other when they drop.
                    neighborTEACHER = getTEACHERAt(boardCopy, x + offsetX, y + offsetY)
                    if neighborTEACHER != None and neighborTEACHER in possibleTEACHERs:
                        possibleTEACHERs.remove(neighborTEACHER)

                newTEACHER = random.choice(possibleTEACHERs)
                boardCopy[x][y] = newTEACHER
                dropSlots[x].append(newTEACHER)
    return dropSlots


def findMatchingTEACHERs(board):
    TEACHERsToRemove = [] # a list of lists of TEACHERs in matching triplets that should be removed
    boardCopy = copy.deepcopy(board)

    # loop through each space, checking for 3 adjacent identical TEACHERs
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
            # look for horizontal matches
            if getTEACHERAt(boardCopy, x, y) == getTEACHERAt(boardCopy, x + 1, y) == getTEACHERAt(boardCopy, x + 2, y) and getTEACHERAt(boardCopy, x, y) != EMPTY_SPACE:
                targetTEACHER = boardCopy[x][y]
                offset = 0
                removeSet = []
                while getTEACHERAt(boardCopy, x + offset, y) == targetTEACHER:
                    # keep checking if there's more than 3 TEACHERs in a row
                    removeSet.append((x + offset, y))
                    boardCopy[x + offset][y] = EMPTY_SPACE
                    offset += 1
                TEACHERsToRemove.append(removeSet)

            # look for vertical matches
            if getTEACHERAt(boardCopy, x, y) == getTEACHERAt(boardCopy, x, y + 1) == getTEACHERAt(boardCopy, x, y + 2) and getTEACHERAt(boardCopy, x, y) != EMPTY_SPACE:
                targetTEACHER = boardCopy[x][y]
                offset = 0
                removeSet = []
                while getTEACHERAt(boardCopy, x, y + offset) == targetTEACHER:
                    # keep checking, in case there's more than 3 TEACHERs in a row
                    removeSet.append((x, y + offset))
                    boardCopy[x][y + offset] = EMPTY_SPACE
                    offset += 1
                TEACHERsToRemove.append(removeSet)

    return TEACHERsToRemove


def highlightSpace(x, y):
    pygame.draw.rect(DISPLAYSURF, HIGHLIGHTCOLOR, BOARDRECTS[x][y], 4)


def getDroppingTEACHERs(board):
    # Find all the TEACHERs that have an empty space below them
    boardCopy = copy.deepcopy(board)
    droppingTEACHERs = []
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT - 2, -1, -1):
            if boardCopy[x][y + 1] == EMPTY_SPACE and boardCopy[x][y] != EMPTY_SPACE:
                # This space drops if not empty but the space below it is
                droppingTEACHERs.append( {'imageNum': boardCopy[x][y], 'x': x, 'y': y, 'direction': DOWN} )
                boardCopy[x][y] = EMPTY_SPACE
    return droppingTEACHERs


def animateMovingTEACHERs(board, TEACHERs, pointsText, score):
    # pointsText is a dictionary with keys 'x', 'y', and 'points'
    progress = 0 # progress at 0 represents beginning, 100 means finished.
    while progress < 100: # animation loop
        DISPLAYSURF.fill(BGCOLOR)
        drawBoard(board)
        for TEACHER in TEACHERs: # Draw each TEACHER.
            drawMovingTEACHER(TEACHER, progress)
        drawScore(score)
        for pointText in pointsText:
            pointsSurf = BASICFONT.render(str(pointText['points']), 1, SCORECOLOR)
            pointsRect = pointsSurf.get_rect()
            pointsRect.center = (pointText['x'], pointText['y'])
            DISPLAYSURF.blit(pointsSurf, pointsRect)

        pygame.display.update()
        FPSCLOCK.tick(FPS)
        progress += MOVERATE # progress the animation a little bit more for the next frame


def moveTEACHERs(board, movingTEACHERs):
    # movingTEACHERs is a list of dicts with keys x, y, direction, imageNum
    for TEACHER in movingTEACHERs:
        if TEACHER['y'] != ROWABOVEBOARD:
            board[TEACHER['x']][TEACHER['y']] = EMPTY_SPACE
            movex = 0
            movey = 0
            if TEACHER['direction'] == LEFT:
                movex = -1
            elif TEACHER['direction'] == RIGHT:
                movex = 1
            elif TEACHER['direction'] == DOWN:
                movey = 1
            elif TEACHER['direction'] == UP:
                movey = -1
            board[TEACHER['x'] + movex][TEACHER['y'] + movey] = TEACHER['imageNum']
        else:
            # TEACHER is located above the board (where new TEACHERs come from)
            board[TEACHER['x']][0] = TEACHER['imageNum'] # move to top row


def fillBoardAndAnimate(board, points, score):
    dropSlots = getDropSlots(board)
    while dropSlots != [[]] * BOARDWIDTH:
        # do the dropping animation as long as there are more TEACHERs to drop
        movingTEACHERs = getDroppingTEACHERs(board)
        for x in range(len(dropSlots)):
            if len(dropSlots[x]) != 0:
                # cause the lowest TEACHER in each slot to begin moving in the DOWN direction
                movingTEACHERs.append({'imageNum': dropSlots[x][0], 'x': x, 'y': ROWABOVEBOARD, 'direction': DOWN})

        boardCopy = getBoardCopyMinusTEACHERs(board, movingTEACHERs)
        animateMovingTEACHERs(boardCopy, movingTEACHERs, points, score)
        moveTEACHERs(board, movingTEACHERs)

        # Make the next row of TEACHERs from the drop slots
        # the lowest by deleting the previous lowest TEACHERs.
        for x in range(len(dropSlots)):
            if len(dropSlots[x]) == 0:
                continue
            board[x][0] = dropSlots[x][0]
            del dropSlots[x][0]


def checkForTEACHERClick(pos):
    # See if the mouse click was on the board
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
            if BOARDRECTS[x][y].collidepoint(pos[0], pos[1]):
                return {'x': x, 'y': y}
    return None # Click was not on the board.


def drawBoard(board):
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
            pygame.draw.rect(DISPLAYSURF, GRIDCOLOR, BOARDRECTS[x][y], 1)
            TEACHERToDraw = board[x][y]
            if TEACHERToDraw != EMPTY_SPACE:
                DISPLAYSURF.blit(TEACHERIMAGES[TEACHERToDraw], BOARDRECTS[x][y])


def getBoardCopyMinusTEACHERs(board, TEACHERs):
    # Creates and returns a copy of the passed board data structure,
    # with the TEACHERs in the "TEACHERs" list removed from it.
    #
    # TEACHERs is a list of dicts, with keys x, y, direction, imageNum

    boardCopy = copy.deepcopy(board)

    # Remove some of the TEACHERs from this board data structure copy.
    for TEACHER in TEACHERs:
        if TEACHER['y'] != ROWABOVEBOARD:
            boardCopy[TEACHER['x']][TEACHER['y']] = EMPTY_SPACE
    return boardCopy


def drawScore(score):
    scoreImg = BASICFONT.render(str(score), 1, SCORECOLOR)
    scoreRect = scoreImg.get_rect()
    scoreRect.bottomleft = (10, WINDOWHEIGHT - 6)
    DISPLAYSURF.blit(scoreImg, scoreRect)


if __name__ == '__main__':
    main()
