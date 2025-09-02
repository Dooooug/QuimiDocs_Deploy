// src/setupTests.js
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// Opcional: Se você usa o Jest e quer configurar algo globalmente para seus testes.
// Por exemplo, para mockar localStorage ou fetch, ou configurar um JSDOM customizado.
// window.localStorage = {
//   getItem: jest.fn(() => null),
//   setItem: jest.fn(),
//   removeItem: jest.fn(),
//   clear: jest.fn(),
// };
// global.fetch = jest.fn(() =>
//   Promise.resolve({
//     json: () => Promise.resolve([]),
//   })
// );
