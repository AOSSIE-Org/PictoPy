import React, { useState } from 'react';
import Webcam from 'react-webcam';
import { Dispatch, SetStateAction } from 'react';
interface WebcamComponentType {
  setShowCamera: Dispatch<SetStateAction<boolean>>;
  setImageUrl: Dispatch<SetStateAction<string | null>>;
}
const videoConstraints = {
  facingMode: 'user',
};
function WebcamComponent({ setShowCamera, setImageUrl }: WebcamComponentType) {
  const webcamRef = React.useRef(null);
  const capture = React.useCallback(() => {
    const imageSrc = webcamRef.current.getScreenshot();
    setImageUrl(imageSrc);
    setShowCamera(false);
  }, [webcamRef]);
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '2rem',
      }}
    >
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '4px',
        }}
      >
        <Webcam
          audio={false}
          height={500}
          ref={webcamRef}
          screenshotFormat="image/jpeg"
          width={500}
          videoConstraints={videoConstraints}
        />
        <button onClick={capture}>Capture photo</button>
      </div>
    </div>
  );
}
export default WebcamComponent;
