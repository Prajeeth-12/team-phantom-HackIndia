import React, { useState } from 'react';

interface DynamicTableProps {
  title: string;
  data: any[];
  actions: string[];
  onAction: (event: string, payload: any) => void;
}

export const DynamicTable: React.FC<DynamicTableProps> = ({ title, data, actions, onAction }) => {
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editFormData, setEditFormData] = useState<any>({});

  if (!data || data.length === 0) return <div className="text-gray-500 italic p-4">No data available in {title}</div>;
  
  const headers = Object.keys(data[0]);

  const handleEditClick = (index: number, row: any) => {
    setEditingIndex(index);
    setEditFormData({ ...row });
  };

  const handleSaveClick = (index: number) => {
    onAction('update_action', editFormData);
    setEditingIndex(null);
  };

  const handleCancelClick = () => {
    setEditingIndex(null);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>, header: string) => {
    setEditFormData({
      ...editFormData,
      [header]: e.target.value
    });
  };

  return (
    <div className="w-full bg-white rounded-lg shadow-sm border border-gray-100 p-4 mb-4">
      {title && <h2 className="text-xl font-bold mb-4 text-slate-800">{title}</h2>}
      <div className="overflow-x-auto rounded-md">
        <table className="min-w-full text-left text-sm whitespace-nowrap">
          <thead className="bg-slate-50 border-b border-gray-200 text-slate-600 uppercase tracking-wider">
            <tr>
              {headers.map(header => (
                <th key={header} className="px-6 py-3 font-medium">{header}</th>
              ))}
              {actions && actions.length > 0 && <th className="px-6 py-3 font-medium text-right">Actions</th>}
            </tr>
          </thead>
          <tbody>
            {data.map((row, index) => (
              <tr key={index} className="border-b border-gray-50 hover:bg-slate-50 transition-colors">
                {headers.map(header => (
                  <td key={header} className="px-6 py-4 text-slate-700">
                    {editingIndex === index && header !== 'id' ? (
                      <input 
                        type="text" 
                        value={editFormData[header] || ''} 
                        onChange={(e) => handleChange(e, header)}
                        className="border border-gray-300 rounded px-2 py-1 w-full text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    ) : (
                      String(row[header])
                    )}
                  </td>
                ))}
                {actions && actions.length > 0 && (
                  <td className="px-6 py-4 space-x-2 text-right">
                    {editingIndex === index ? (
                      <>
                        <button
                          onClick={() => handleSaveClick(index)}
                          className="px-3 py-1.5 bg-green-50 text-green-700 hover:bg-green-100 rounded text-xs font-semibold transition inline-block mr-2"
                        >
                          Save
                        </button>
                        <button
                          onClick={handleCancelClick}
                          className="px-3 py-1.5 bg-gray-50 text-gray-700 hover:bg-gray-100 rounded text-xs font-semibold transition inline-block"
                        >
                          Cancel
                        </button>
                      </>
                    ) : (
                      actions.map(action => (
                        <button
                          key={action}
                          onClick={() => {
                            if (action.toLowerCase() === 'edit') {
                              handleEditClick(index, row);
                            } else {
                              onAction(`${action}_action`, row);
                            }
                          }}
                          className="px-3 py-1.5 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 rounded text-xs font-semibold transition mr-2 last:mr-0 inline-block"
                        >
                          {action}
                        </button>
                      ))
                    )}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
