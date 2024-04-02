import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

const Navbar = ({ title, leftButton, rightButton }) => {
  return (
    <View style={styles.navbar}>
      {leftButton && (
        <TouchableOpacity onPress={leftButton.onPress}>
          <Text style={styles.button}>{leftButton.title}</Text>
        </TouchableOpacity>
      )}
      <Text style={styles.title}>{title}</Text>
      {rightButton && (
        <TouchableOpacity onPress={rightButton.onPress}>
          <Text style={styles.button}>{rightButton.title}</Text>
        </TouchableOpacity>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  navbar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#3498db',
    padding: 10,
  },
  title: {
    fontSize: 20,
    color: '#fff',
  },
  button: {
    fontSize: 16,
    color: '#fff',
  },
});

export default Navbar;
