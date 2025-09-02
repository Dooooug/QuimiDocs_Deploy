// src/pages/Products/ProductListPage.js
import React, { useEffect, useState, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  getPaginationRowModel,
  getFilteredRowModel,
  getSortedRowModel,
} from '@tanstack/react-table';
import productService from '../../services/productService';
import PopupMessage from '../../components/Common/PopupMessage';
import useAuth from '../../hooks/useAuth';
import { ROLES } from '../../utils/constants';

import '../../styles/ProductListPage.css';

function ProductListPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState('');
  const [showMessage, setShowMessage] = useState(false);
  const [globalFilter, setGlobalFilter] = useState('');

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const data = await productService.getProducts();

        const processedProducts = (data || []).map((p) => {
          const productId = String(p.id || p._id || `temp-${Math.random().toString(36).substring(2, 9)}`);
          return {
            ...p,
            id: productId,
          };
        });

        const filteredApprovedProducts = processedProducts.filter((p) => p.status === 'aprovado');
        setProducts(filteredApprovedProducts);
        setLoading(false);
      } catch (err) {
        console.error('Erro ao buscar produtos:', err);
        setError('Erro ao carregar produtos. Tente novamente mais tarde.');
        setMessage('Erro ao carregar produtos: ' + (err.response?.data?.msg || 'Verifique sua conexão.'));
        setShowMessage(true);
        setLoading(false);
      }
    };

    if (user) {
      fetchProducts();
    }
  }, [user]);

  const handleDelete = useCallback(async (productId) => {
    if (!window.confirm('Tem certeza que deseja excluir este produto?')) {
      return;
    }
    try {
      await productService.deleteProduct(productId);
      setProducts((prevProducts) => prevProducts.filter((product) => product.id !== productId));
      setMessage('Produto excluído com sucesso!');
      setShowMessage(true);
    } catch (err) {
      console.error('Erro ao excluir produto:', err);
      setMessage('Erro ao excluir produto: ' + (err.response?.data?.msg || 'Você não tem permissão para esta ação.'));
      setShowMessage(true);
    }
  }, []);

  const handleEdit = useCallback((productId) => {
    navigate(`/app/products/edit/${productId}`);
  }, [navigate]);

  const columns = useMemo(
    () => [
      {
        accessorKey: 'codigo',
        header: 'Código',
        cell: (info) => info.getValue(),
      },
      {
        accessorKey: 'nome_do_produto',
        header: 'Nome do Produto',
        cell: (info) => info.getValue(),
      },
      {
        accessorKey: 'fornecedor',
        header: 'Fornecedor',
        cell: (info) => info.getValue(),
      },
      {
        accessorKey: 'status',
        header: 'Status',
        cell: (info) => info.getValue(),
      },
      {
        accessorKey: 'created_at',
        header: 'Data de Cadastro',
        cell: (info) => {
          const raw = info.getValue();
          const date = raw ? new Date(raw) : null;
          return date ? date.toLocaleDateString('pt-BR') : '—';
        },
      },
      {
        accessorKey: 'created_by',
        header: 'Criado Por',
        cell: (info) => info.getValue() || '—',
      },
      {
        accessorKey: 'pdf_url',
        header: 'FISPQ',
        cell: (info) =>
          info.getValue() ? (
            <a href={info.getValue()} target="_blank" rel="noopener noreferrer">
              Ver FISPQ
            </a>
          ) : (
            'N/A'
          ),
      },
      {
        id: 'actions',
        header: 'Ações',
        cell: (info) => (
          <div className="table-actions">
            {(user &&
              (user.role === ROLES.ADMIN ||
                (user.role === ROLES.ANALYST &&
                  info.row.original.created_by_user_id === user.id &&
                  info.row.original.status !== 'aprovado'))) && (
              <button onClick={() => handleEdit(info.row.original.id)} className="edit-button">
                Editar
              </button>
            )}
            {user && user.role === ROLES.ADMIN && (
              <button onClick={() => handleDelete(info.row.original.id)} className="delete-button">
                Excluir
              </button>
            )}
          </div>
        ),
      },
    ],
    [user, handleEdit, handleDelete]
  );

  const table = useReactTable({
    data: products,
    columns,
    state: {
      globalFilter,
    },
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    initialState: {
      pagination: { pageSize: 10 },
    },
  });

  if (loading) {
    return (
      <div className="product-list-page">
        <h1>Produtos Cadastrados</h1>
        <p>Carregando produtos...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="product-list-page error-message">
        <h1>Produtos Cadastrados</h1>
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="product-list-page">
      <h1>Produtos Cadastrados</h1>
      <p>Lista de todos os produtos na base de dados.</p>

      <div className="search-and-pagination">
        <input
          type="text"
          placeholder="Pesquisar em todos os campos..."
          value={globalFilter ?? ''}
          onChange={(e) => setGlobalFilter(e.target.value)}
          className="global-filter-input"
        />
        <div>
          <button
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
            className="pagination-button"
          >
            Anterior
          </button>
          <span className="pagination-info">
            Página{' '}
            <strong>
              {table.getState().pagination.pageIndex + 1} de {table.getPageCount()}
            </strong>{' '}
            ({table.getFilteredRowModel().rows.length} itens)
          </span>
          <button
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
            className="pagination-button"
          >
            Próximo
          </button>
          <select
            value={table.getState().pagination.pageSize}
            onChange={(e) => {
              table.setPageSize(Number(e.target.value));
            }}
            className="page-size-select"
          >
            {[10, 20, 30, 40, 50].map((pageSize) => (
              <option key={pageSize} value={pageSize}>
                Mostrar {pageSize}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="table-container">
        <table className="product-table">
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th key={header.id} colSpan={header.colSpan}>
                    {header.isPlaceholder ? null : (
                      <div
                        className={header.column.getCanSort() ? 'cursor-pointer select-none' : ''}
                        onClick={header.column.getToggleSortingHandler()}
                      >
                        {flexRender(header.column.columnDef.header, header.getContext())}
                        {{
                          asc: ' 🔼',
                          desc: ' 🔽',
                        }[header.column.getIsSorted()] ?? null}
                      </div>
                    )}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.length > 0 ? (
              table.getRowModel().rows.map((row) => (
                <tr key={row.id}>
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={columns.length} style={{ textAlign: 'center' }}>
                  Nenhum produto encontrado.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {showMessage && (
        <PopupMessage
          message={message}
          onClose={() => setShowMessage(false)}
          type={message.includes('sucesso') ? 'success' : 'error'}
        />
      )}
    </div>
  );
}

export default ProductListPage;
