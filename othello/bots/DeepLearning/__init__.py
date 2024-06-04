import numpy as np
from othello.OthelloUtil import getValidMoves
from othello.bots.DeepLearning.OthelloModel import OthelloModel
from othello.OthelloGame import OthelloGame

class BOT():

    def __init__(self, board_size, *args, **kargs):
        self.board_size = board_size
        self.model = OthelloModel(input_shape=(self.board_size, self.board_size))
        try:
            self.model.load_model()
            print('Model loaded')
        except:
            print('No model exists')
            pass
        
        self.collect_gaming_data = False
        self.history = []
        self.win_loss_record = {'win': 0, 'lose': 0, 'draw': 0}

    def getAction(self, game, color):
        predict = self.model.predict(game)
        predict += 1e-30
        # print("predict_result", predict)
        valid_positions = getValidMoves(game, color)
        valids = np.zeros((game.size), dtype='int')
        valids[[i[0] * self.board_size + i[1] for i in valid_positions]] = 1
        predict *= valids
        position = np.argmax(predict)
        
        if self.collect_gaming_data:
            tmp = np.zeros_like(predict)
            tmp[position] = 1.0
            self.history.append([np.array(game.copy()), tmp, color])

        position = (position // self.board_size, position % self.board_size)
        return position

    def record_result(self, result):
        if result == 1:
            self.win_loss_record['win'] += 1
        elif result == -1:
            self.win_loss_record['lose'] += 1
        else:
            self.win_loss_record['draw'] += 1

    def print_win_loss_percentage(self):
        total_games = self.win_loss_record['win'] + self.win_loss_record['lose'] + self.win_loss_record['draw']
        if total_games > 0:
            win_percentage = (self.win_loss_record['win'] / total_games) * 100
            lose_percentage = (self.win_loss_record['lose'] / total_games) * 100
            draw_percentage = (self.win_loss_record['draw'] / total_games) * 100
            print(f"Win Percentage: {win_percentage:.2f}%")
            print(f"Lose Percentage: {lose_percentage:.2f}%")
            print(f"Draw Percentage: {draw_percentage:.2f}%")
        else:
            print("No games recorded yet.")

    def self_play_train(self, args):
        self.collect_gaming_data = True

        def gen_data():
            def getSymmetries(board, pi):
                pi_board = np.reshape(pi, (len(board), len(board)))
                l = []
                for i in range(1, 5):
                    for j in [True, False]:
                        newB = np.rot90(board, i)
                        newPi = np.rot90(pi_board, i)
                        if j:
                            newB = np.fliplr(newB)
                            newPi = np.fliplr(newPi)
                        l += [(newB, list(newPi.ravel()))]
                return l

            self.history = []
            history = []
            game = OthelloGame(self.board_size)
            game.play(self, self, verbose=args['verbose'])
            for step, (board, probs, player) in enumerate(self.history):
                sym = getSymmetries(board, probs)
                for b, p in sym:
                    history.append([b, p, player])
            self.history.clear()
            game_result = game.isEndGame()
            self.record_result(game_result)
            return [(x[0], x[1]) for x in history if (game_result == 0 or x[2] == game_result)]

        data = []
        for i in range(args['num_of_generate_data_for_train']):
            if args['verbose']:
                print('Self playing', i + 1)
            data += gen_data()

        self.collect_gaming_data = False
        self.model.fit(data, batch_size=args['batch_size'], epochs=args['epochs'])
        self.model.save_model()
        self.print_win_loss_percentage()
