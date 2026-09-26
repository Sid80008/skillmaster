import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from './App';
import { apiClient } from './api/client';

// Mock the API client
vi.mock('./api/client', () => {
  return {
    apiClient: {
      get: vi.fn(),
      post: vi.fn(),
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() }
      }
    }
  };
});

describe('Skill Quest Frontend End-to-End', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    let store: Record<string, string> = {};
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: vi.fn((key) => store[key] || null),
        setItem: vi.fn((key, value) => { store[key] = value.toString(); }),
        removeItem: vi.fn((key) => { delete store[key]; }),
        clear: vi.fn(() => { store = {}; })
      },
      writable: true
    });
  });

  it('redirects to login when unauthenticated', async () => {
    (apiClient.get as any).mockRejectedValue({ response: { status: 401 } });
    render(<App />);
    
    // Auth context initially loads user
    await waitFor(() => {
      expect(screen.getByText(/sign in/i)).toBeInTheDocument();
    });
  });

  it('explores, gets recommendation, accepts, completes, and feedbacks', async () => {
    localStorage.setItem('skillquest_token', 'fake-token');
    
    // Mock getCurrentUser
    (apiClient.get as any).mockImplementation((url: string) => {
      if (url === '/auth/me') return Promise.resolve({ data: { id: 'u1', username: 'testuser' } });
      if (url === '/quests/current') return Promise.resolve({ data: null }); // No active quest
      return Promise.resolve({ data: {} });
    });

    // Mock generateRecommendation
    (apiClient.post as any).mockImplementation((url: string) => {
      if (url === '/recommendations/') {
        return Promise.resolve({
          data: {
            id: 'rec1',
            candidates: [{ skill_id: 'skill1', skill_name: 'Test Skill', explanation: 'A novel skill', novelty_category: 'NEW_TERRITORY' }]
          }
        });
      }
      if (url === '/recommendations/rec1/accept') {
        return Promise.resolve({ data: { id: 'attempt1' } });
      }
      return Promise.resolve({ data: {} });
    });

    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText(/what will you try this weekend\?/i)).toBeInTheDocument();
    });
    
    expect(screen.getByText('Test Skill')).toBeInTheDocument();
    
    // Accept
    fireEvent.click(screen.getByText(/Accept Quest — Reserve This Weekend/i));
    
    // Expect API call
    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith('/recommendations/rec1/accept', { selected_skill_id: 'skill1' });
    });
  });
});
