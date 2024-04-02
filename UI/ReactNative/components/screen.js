import React from 'react';
import { View, Text } from 'react-native';
import Navbar from './Navbar'; // Assuming Navbar component is in the same directory

const YourScreen = () => {
  const handleLeftButtonPress = () => {
    // handle left button press action
  };

  const handleRightButtonPress = () => {
    // handle right button press action
  };

  return (
    <View>
      <Navbar 
        title="Your Screen Title"
        leftButton={{
          title: 'Back',
          onPress: handleLeftButtonPress,
        }}
        rightButton={{
          title: 'Options',
          onPress: handleRightButtonPress,
        }}
      />
      {/* Your screen content */}
      <Text>Your Screen Content Goes Here</Text>
    </View>
  );
};

export default YourScreen;
