from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, Dense, Flatten, BatchNormalization, Activation, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
import numpy as np

class OthelloModel():
    def __init__(self, input_shape=(10,10)):
        self.model_name = 'model_' + ('x'.join(list(map(str, input_shape)))) + '.h5'
        self.model = self.build_model(input_shape)
        self.model.compile(loss='categorical_crossentropy', optimizer=Adam(0.002))

    def build_model(self, input_shape):
        model = Sequential()
        model.add(Conv2D(64, kernel_size=3, padding='same', input_shape=input_shape+(1,)))
        model.add(BatchNormalization())
        model.add(Activation('relu'))
        model.add(Dropout(0.3))
        model.add(Conv2D(64, kernel_size=3, padding='same'))
        model.add(BatchNormalization())
        model.add(Activation('relu'))
        model.add(Dropout(0.3))
        model.add(Conv2D(64, kernel_size=3, padding='same'))
        model.add(BatchNormalization())
        model.add(Activation('relu'))
        model.add(Flatten())
        model.add(Dense(256, activation='relu'))
        model.add(Dropout(0.5))
        model.add(Dense(input_shape[0] * input_shape[1], activation='softmax'))
        return model

    def predict(self, board):
        return self.model.predict(np.array([board]).astype('float32'))[0]

    def fit(self, data, batch_size, epochs):
        input_boards, target_policies = list(zip(*data))
        input_boards = np.array(input_boards)
        target_policies = np.array(target_policies)

        # Callbacks
        early_stopping = EarlyStopping(monitor='loss', patience=10, restore_best_weights=True)
        reduce_lr = ReduceLROnPlateau(monitor='loss', factor=0.5, patience=5, min_lr=1e-6)

        self.model.fit(
            x=input_boards, 
            y=target_policies, 
            batch_size=batch_size, 
            epochs=epochs, 
            callbacks=[early_stopping, reduce_lr]
        )

    def save_model(self):
        self.model.save('othello/bots/DeepLearning/models/' + self.model_name)

    def load_model(self):
        self.model.load('othello/bots/DeepLearning/models/' + self.model_name)
