from __future__ import print_function

from keras.layers import Conv1D, MaxPooling1D, Embedding
from keras.layers import Dense, Flatten, Dropout,  LSTM, Bidirectional
from keras.layers import merge
from keras.models import Model
from keras.engine import Input, Merge
from att_layer import AttLayer
import sys

def model_selector(params, args, nb_classes, embedding_matrix):
    """

    :param params:
    :param args:
    :param nb_classes:
    :param embedding_matrix:
    :return:
    Method to select the model to be used for classification
    """
    if (args.exp_name.lower() == 'cnn'):
        return _kim_cnn_model(params, args, nb_classes, embedding_matrix)
    elif (args.exp_name.lower() == 'lstm'):
        return _lstm_model(params, args, nb_classes, embedding_matrix)
    elif (args.exp_name.lower() == 'attn'):
        return _attn_model(params, args, nb_classes, embedding_matrix)
    else:
        print('wrong exp_name')
        sys.exit()

def _attn_model(params, args, nb_classes, embedding_matrix):
    """
    attention-based BD LSTM-RNN
    :param args:
    :param embedding_matrix:
    :return:
    """

    lstm_hs = params['lstm_hs']
    use_embeddings = params['use_embeddings']
    embeddings_trainable = params['embeddings_trainable']

    input = Input(shape=(args.max_sequence_len,), dtype='int32', name="input")
    aux = Input(shape=(1,), dtype='float32', name="aux")
    len_feat = Dense(1, activation='softmax')(aux)

    if (use_embeddings):
        embedding_layer = Embedding(args.nb_words + 1,
                                    args.embedding_dim,
                                    weights=[embedding_matrix],
                                    input_length=args.max_sequence_len,
                                    trainable=embeddings_trainable)(input)
    else:
        embedding_layer = Embedding(args.nb_words + 1,
                                    args.embedding_dim,
                                    weights=None,
                                    input_length=args.max_sequence_len,
                                    trainable=embeddings_trainable)(input)

    x = Dropout(params['dropout1'])(embedding_layer)
    # based on two_LSTM, setup network.
    if(params['two_LSTM']):
        x = Bidirectional(LSTM(lstm_hs, dropout_W=0.2, dropout_U=0.2, return_sequences=True))(x)
        x = Bidirectional(LSTM(lstm_hs, dropout_W=0.2, dropout_U=0.2, return_sequences=True))(x)
    else:
        x = Bidirectional(LSTM(lstm_hs, dropout_W=0.2, dropout_U=0.2, return_sequences=True))(x)
    x = AttLayer()(x)
    x = Dropout(params['dropout2'])(x)

    x = merge([x, len_feat], mode='concat')

    result = Dense(nb_classes, activation='softmax')(x)
    model = Model(input=[input, aux], output=result)
    model.compile(loss='categorical_crossentropy',
                  optimizer=params['optimizer'],
                  metrics=['acc'])
    print(model.summary())
    return model


def _lstm_model(params, args, nb_classes, embedding_matrix):
    """
    BD LSTM-RNN
    :param args:
    :param embedding_matrix:
    :return:
    """

    lstm_hs = params['lstm_hs']
    use_embeddings = params['use_embeddings']
    embeddings_trainable = params['embeddings_trainable']

    input = Input(shape=(args.max_sequence_len,), dtype='int32', name="input")
    aux = Input(shape=(1,), dtype='float32', name="aux")
    len_feat = Dense(1, activation='softmax')(aux)

    if (use_embeddings):
        embedding_layer = Embedding(args.nb_words + 1,
                                    args.embedding_dim,
                                    weights=[embedding_matrix],
                                    input_length=args.max_sequence_len,
                                    trainable=embeddings_trainable)(input)
    else:
        embedding_layer = Embedding(args.nb_words + 1,
                                    args.embedding_dim,
                                    weights=None,
                                    input_length=args.max_sequence_len,
                                    trainable=embeddings_trainable)(input)

    x = Dropout(params['dropout1'])(embedding_layer)
    # based on two_LSTM, setup network.
    if(params['two_LSTM']):
        x = Bidirectional(LSTM(lstm_hs, dropout_W=0.2, dropout_U=0.2, return_sequences=True))(x)
        x = Bidirectional(LSTM(lstm_hs, dropout_W=0.2, dropout_U=0.2))(x)
    else:
        x = Bidirectional(LSTM(lstm_hs, dropout_W=0.2, dropout_U=0.2))(x)
    x = Dropout(params['dropout2'])(x)

    x = merge([x, len_feat], mode='concat')
    result = Dense(nb_classes, activation='softmax')(x)
    model = Model(input=[input, aux], output=result)
    model.compile(loss='categorical_crossentropy',
                  optimizer=params['optimizer'],
                  metrics=['acc'])
    print(model.summary())
    return model


def _kim_cnn_model(params, args, nb_classes, embedding_matrix):
    """
    fully functional API style so that we can see all model details.
    params will obtain model related parameters

    :param params:
    :param args:
    :param nb_classes: # of labels to classify
    :param embedding_matrix:
    :return: a compiled Keras model
    """
    nb_filter = params['nb_filter']
    use_embeddings = params['use_embeddings']
    embeddings_trainable = params['embeddings_trainable']

    input = Input(shape=(args.max_sequence_len,), dtype='int32', name="input")
    aux = Input(shape=(1,), dtype='float32', name="aux")
    len_feat = Dense(1, activation='softmax')(aux)

    if (use_embeddings):
        embedding_layer = Embedding(args.nb_words + 1,
                                    args.embedding_dim,
                                    weights=[embedding_matrix],
                                    input_length=args.max_sequence_len,
                                    trainable=embeddings_trainable)(input)
    else:
        embedding_layer = Embedding(args.nb_words + 1,
                                    args.mbedding_dim,
                                    weights=None,
                                    input_length=args.max_sequence_len,
                                    trainable=embeddings_trainable)(input)
    embedding_layer = Dropout(params['dropout1'])(embedding_layer)

    filtersize = params['filter_size']
    filtersize_list = [filtersize - 1, filtersize, filtersize + 1]
    conv_list = []
    for index, filtersize in enumerate(filtersize_list):
        pool_length = args.max_sequence_len - filtersize + 1
        conv = Conv1D(nb_filter=nb_filter, filter_length=filtersize, activation='relu')(embedding_layer)
        pool = MaxPooling1D(pool_length=pool_length)(conv)
        flatten = Flatten()(pool)
        conv_list.append(flatten)

    if (len(filtersize_list) > 1):
        conv_out = Merge(mode='concat', concat_axis=1)(conv_list)
    else:
        conv_out = conv_list[0]

    x = Dropout(params['dropout2'])(conv_out)
    x = merge([x, len_feat], mode='concat')
    result = Dense(nb_classes, activation='softmax')(x)

    model = Model(input=[input, aux], output=result)
    model.compile(loss='categorical_crossentropy',
                  optimizer=params['optimizer'],
                  metrics=['acc'])
    print(model.summary())
    return model
