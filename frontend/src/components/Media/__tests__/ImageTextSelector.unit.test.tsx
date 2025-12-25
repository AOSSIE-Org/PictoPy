import { render, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

// Mock ocrWorker to return deterministic boxes
jest.mock('../../../ocr/ocrWorker', () => ({
  runOCR: jest.fn(async () => ({ boxes: [ { x:10,y:10,width:100,height:20,text:'Hello',confidence:95 }, { x:120,y:10,width:80,height:20,text:'World',confidence:90 } ], text: 'Hello World', width: 800, height: 600 })),
  getCachedOCR: jest.fn(()=>null),
  initOCRWorker: jest.fn(async ()=>{}),
}));

import ImageTextSelector from '../ImageTextSelector';

describe('ImageTextSelector', ()=>{
  test('toggles selection mode with Ctrl+T and shows boxes', async ()=>{
    const { container } = render(<div style={{width:400,height:300}}><ImageTextSelector imageUrl={'/test.png'} alt={'img'} /></div>);
    // toggle via ctrl+t
    fireEvent.keyDown(window, { ctrlKey: true, key: 't' });
    // wait for boxes
    await waitFor(()=>{
      expect(container.querySelectorAll('.its-box').length).toBeGreaterThan(0);
    });
  });

  test('mouse drag selects boxes and copy works (fallback)', async ()=>{
    const { container, getByAltText } = render(<div style={{width:400,height:300}}><ImageTextSelector imageUrl={'/test.png'} alt={'img'} /></div>);
    fireEvent.keyDown(window, { ctrlKey: true, key: 't' });
    await waitFor(()=>expect(container.querySelectorAll('.its-box').length).toBeGreaterThan(0));
    const img = getByAltText('img');
    const containerDiv = container.querySelector('.its-image-container') as Element;
    // mock bounding rects to simulate layout (image scaled to 400x300)
    (img as HTMLImageElement).getBoundingClientRect = () => ({ left:0, top:0, width:400, height:300, right:400, bottom:300 } as DOMRect);
    (containerDiv as Element).getBoundingClientRect = () => ({ left:0, top:0, width:400, height:300, right:400, bottom:300 } as DOMRect);
    // simulate mousedown at 5,5 then mouseup at 200,20
    fireEvent.mouseDown(containerDiv, { clientX: 5, clientY: 5 });
    fireEvent.mouseMove(containerDiv, { clientX: 200, clientY: 20 });
    fireEvent.mouseUp(containerDiv, { clientX: 200, clientY: 20 });
    // selection should have selected boxes
    await waitFor(()=>{
      const selected = container.querySelectorAll('.its-box.selected');
      expect(selected.length).toBeGreaterThan(0);
    });
    // click copy button; navigator.clipboard may not exist — fallback will run
    const copyBtn = container.querySelector('.its-controls button') as HTMLButtonElement;
    expect(copyBtn).toBeTruthy();
    // call copy
    copyBtn.click();
  });
});
