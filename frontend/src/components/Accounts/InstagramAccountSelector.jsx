import React, { useState, useEffect } from 'react';
import { Instagram, CheckCircle, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';

/**
 * Instagram Account Selector Component
 *
 * Allows users to select which Instagram Business Account to connect
 * when they have multiple Facebook Pages with Instagram accounts.
 *
 * Permissions demonstrated:
 * - pages_show_list: Lists Facebook Pages
 * - instagram_business_basic: Gets Instagram account info
 */
const InstagramAccountSelector = ({ onSelect, onCancel }) => {
  const [pages, setPages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedPage, setSelectedPage] = useState(null);

  useEffect(() => {
    fetchPages();
  }, []);

  const fetchPages = async () => {
    try {
      setLoading(true);

      // This would typically call your backend which uses the Instagram Graph API
      // to get the list of pages with Instagram accounts
      const response = await fetch('/api/v1/instagram/pages', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch Instagram accounts');
      }

      const data = await response.json();
      setPages(data.pages || []);

      // Auto-select if only one page
      if (data.pages && data.pages.length === 1) {
        setSelectedPage(data.pages[0]);
      }
    } catch (error) {
      console.error('Error fetching pages:', error);
      toast.error('Failed to load Instagram accounts');
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = () => {
    if (!selectedPage) {
      toast.error('Please select an Instagram account');
      return;
    }

    onSelect(selectedPage);
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">Loading Instagram accounts...</span>
        </div>
      </div>
    );
  }

  if (pages.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="text-center py-8">
          <AlertCircle className="mx-auto h-12 w-12 text-yellow-500 mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            No Instagram Business Accounts Found
          </h3>
          <p className="text-gray-600 mb-6">
            To connect your Instagram account, you need:
          </p>
          <ul className="text-left max-w-md mx-auto mb-6 space-y-2">
            <li className="flex items-start">
              <span className="text-blue-600 mr-2">•</span>
              <span className="text-gray-700">
                An Instagram Business or Creator account
              </span>
            </li>
            <li className="flex items-start">
              <span className="text-blue-600 mr-2">•</span>
              <span className="text-gray-700">
                A Facebook Page linked to your Instagram account
              </span>
            </li>
            <li className="flex items-start">
              <span className="text-blue-600 mr-2">•</span>
              <span className="text-gray-700">
                Admin access to both the Page and Instagram account
              </span>
            </li>
          </ul>
          <div className="space-y-2">
            <a
              href="https://www.facebook.com/business/help/1492627900875762"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block text-blue-600 hover:text-blue-700 font-medium"
            >
              Learn how to convert to a Business account →
            </a>
            <br />
            <a
              href="https://www.facebook.com/business/help/898752960195806"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block text-blue-600 hover:text-blue-700 font-medium"
            >
              Learn how to link Instagram to a Facebook Page →
            </a>
          </div>
          <button
            onClick={onCancel}
            className="mt-6 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Select Instagram Account
        </h2>
        <p className="text-gray-600">
          {pages.length === 1
            ? 'We found 1 Instagram Business account connected to your Facebook Pages.'
            : `We found ${pages.length} Instagram Business accounts. Select the one you want to connect.`}
        </p>
      </div>

      <div className="space-y-3 mb-6">
        {pages.map((page) => (
          <div
            key={page.instagram_account_id}
            onClick={() => setSelectedPage(page)}
            className={`
              relative border-2 rounded-lg p-4 cursor-pointer transition-all
              ${selectedPage?.instagram_account_id === page.instagram_account_id
                ? 'border-blue-600 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300 bg-white'
              }
            `}
          >
            <div className="flex items-center">
              <div className="flex-shrink-0">
                {page.profile_picture_url ? (
                  <img
                    src={page.profile_picture_url}
                    alt={page.username}
                    className="h-12 w-12 rounded-full object-cover"
                  />
                ) : (
                  <div className="h-12 w-12 rounded-full bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center">
                    <Instagram className="h-6 w-6 text-white" />
                  </div>
                )}
              </div>

              <div className="ml-4 flex-grow">
                <div className="flex items-center">
                  <Instagram className="h-4 w-4 text-gray-400 mr-2" />
                  <p className="font-semibold text-gray-900">
                    @{page.username}
                  </p>
                </div>
                {page.name && (
                  <p className="text-sm text-gray-600 mt-1">
                    {page.name}
                  </p>
                )}
                <p className="text-xs text-gray-500 mt-1">
                  Facebook Page: {page.page_name}
                </p>
                {page.followers_count !== undefined && (
                  <p className="text-xs text-gray-500">
                    {page.followers_count.toLocaleString()} followers
                  </p>
                )}
              </div>

              {selectedPage?.instagram_account_id === page.instagram_account_id && (
                <div className="flex-shrink-0 ml-4">
                  <CheckCircle className="h-6 w-6 text-blue-600" />
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="flex justify-end space-x-3">
        <button
          onClick={onCancel}
          className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={handleConnect}
          disabled={!selectedPage}
          className={`
            px-6 py-2 rounded-lg font-medium transition-colors
            ${selectedPage
              ? 'bg-blue-600 text-white hover:bg-blue-700'
              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }
          `}
        >
          Connect Selected Account
        </button>
      </div>

      {selectedPage && (
        <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-800">
            <strong>Selected:</strong> @{selectedPage.username} ({selectedPage.page_name})
          </p>
        </div>
      )}
    </div>
  );
};

export default InstagramAccountSelector;
