import os
import csv
import time
import random
import numpy as np
from tqdm import tqdm
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Conv2D, Flatten


def normalize_data(inpath):
	# read in data from csv
	f = open(inpath, 'r+')
	csv_reader = csv.reader(f)
	header = next(csv_reader)
	data = []
	for row in csv_reader:
		if '' in row:
			continue
		# remove team name
		row.pop(0)
		# remove gp (always 82)
		row.pop(0)
		# remove the w l and otl columns
		for i in range(3):
			row.pop(-4)
		# track the rest of the data
		data.append(row)

	# normalize all values to the range [0,1)
	# find the upper bound on each column
	maxes = []
	for i in range(len(data[0])):
		maxes.append(0)
	for i in range(len(data)):
		for ii in range(len(data[i])):
			if float(data[i][ii]) > maxes[ii]:
				maxes[ii] = float(data[i][ii])
	for i in range(len(maxes)):
		maxes[i] += 1
	
	# scale all values (expect for pts%, the output) so that the upper bound is 1
	for i in range(len(data)):
		for ii in range(len(data[i])):
			if ii == len(data[i])-1:
				data[i][ii] = float(data[i][ii])
			else:
				data[i][ii] = float(data[i][ii]) / maxes[ii]

	# split up data into x and y, train and test
	x_train = []
	y_train = []
	x_test = []
	y_test = []
	random.shuffle(data)
	for i in range(len(data)):
		y_train.append([data[i][-1]])
		x_train.append([data[i][:-1]])

	val_cut = int(len(x_train)*0.3)
	test_cut = int(len(x_train)*0.1)
	x_test = x_train[-test_cut:]
	x_val = x_train[-val_cut:-test_cut]
	x_train = x_train[:-val_cut]
	y_test = y_train[-test_cut:]
	y_val = y_train[-val_cut:-test_cut]
	y_train = y_train[:-val_cut]
	print(len(x_train), len(x_val), len(x_test))

	# return train and val data, and maxes for future scaling
	return np.array(x_train), np.array(y_train), np.array(x_val), np.array(y_val), x_test, y_test, maxes


def build_model(num_inputs):
	"""
	Builds a simple CNN for character recognition
	"""
	model = Sequential([
		Flatten(input_shape=num_inputs),
		Dense(16, activation=tf.nn.relu),
		Dense(1, activation=tf.keras.activations.linear)
		])
	#print(model.summary())
	return model


def build_and_train_model():
	# extract training data
	x_train, y_train, x_val, y_val, x_test, y_test, maxes = normalize_data('./scraped_nhl_data.csv')

	# build the model
	model = build_model(x_train[0].shape)

	# compile the model
	model.compile(
	    #optimizer=keras.optimizers.Adam(learning_rate=0.000005),
	    optimizer=keras.optimizers.Adam(learning_rate=0.05),
	    loss='mean_squared_error',
	    metrics=['mean_absolute_error']
	)

	# train the model
	model.fit(
	    x_train,
	    y_train,
	    batch_size=64,
	    epochs=80,
	    shuffle=True,
	    validation_data=(x_val, y_val),
	)

	# save the model
	model.save("./nhl_predictor")

	# test the saved model
	model = keras.models.load_model('./nhl_predictor/')
	tot_error = 0
	max_error = 0
	for i in range(len(x_test)):
		out = model.predict([x_test[i]])
		out = out[0][0]
		err = abs(out-y_test[i][0])
		tot_error += err
		max_error = max(err, max_error)

	avg_err, avg_err_pts, max_err = tot_error/len(x_test), (tot_error/len(x_test))*164, max_error*164
	print("Trained model had an average error of {:.2f} ({:.2f} points). Largest error was {:.2f} points".format(avg_err, avg_err_pts, max_err))


def normalize_array(array, maxes):
	for i in range(len(array[0])):
		array[0][i] = float(array[0][i]) / maxes[i]
	return np.array([array])


def reverse_normalize(array, maxes):
	for i in range(len(array[0])):
		array[0][i] = float(array[0][i]) * maxes[i]
	return array


def predict(vals, normalize=True):
	x_train, y_train, x_val, y_val, maxes = normalize_data('./scraped_nhl_data.csv')
	if normalize:
		vals = normalize_array(vals, maxes)
	model = keras.models.load_model('./nhl_predictor/')
	out = model.predict(vals)
	print(out)


if __name__ == "__main__":
	build_and_train_model()