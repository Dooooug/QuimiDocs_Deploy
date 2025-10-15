// src/pages/Products/ProductEditPage.js
import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import productService from '../../services/productService';
import PopupMessage from '../../components/Common/PopupMessage';
import useAuth from '../../hooks/useAuth';
import { ROLES } from '../../utils/constants';

// IMAGENS GHS (Reutilizadas da página de cadastro)
import explosivoImg from '../../assets/explosivo.png';
import gasPressaoImg from '../../assets/gas_pressao.png';
import inflamavelImg from '../../assets/inflamavel.png';
import corrosivoImg from '../../assets/corrosivo.png';
import irritacaoImg from '../../assets/Irritacao.png';
import cancerImg from '../../assets/cancer.png';
import MeioAmbienteImg from '../../assets/meio_ambiente.png';
import MorteImg from '../../assets/morte.png';
import OxidanteImg from '../../assets/oxidante.png';

// Estilo (Reutilizando o mesmo CSS)
import '../../styles/productform.css';

// LISTAS DE SELEÇÃO (Reutilizadas da página de cadastro)
const empresas = [
    'AMARIS DO BRASIL ASSESSORIA EMPRESARIAL', 'AMG - SOLUCOES INDUSTRIAIS', 'BANCO ITAÚ S/A', 'BRAVO SERV. LOG. LTDA - FÁBRICA',
    'CALMITEC CALDEIRARIA E MONTAGENS INDUSTRIAIS', 'CAVALCANTI & ANDRADE ENGENHARIA E CONSULTORIA INDUSTRIAL', 'CONNECTIS TECNOLOGIA DA INFORMAÇÃO E COMUNICAÇÃO DO BRASIL',
    'DATUM K ENGENHARIA', 'ECOSCIENCES - SOLUCOES AMBIENTAIS', 'EMPLOYER ORGANIZAÇÃO DE RECURSOS HUMANOS S.A', 'EMPLOYER RURAL', 'ENTERPRISE SERVICES BRASIL SERVICOS DE TECNOLOGIA',
    'EOLIVEIRA SERVICOS', 'FERNANDO DA SILVA DE OLIVEIRA CONSTRUCOES', 'FLP CORREA TRANSPORTES', 'FM2C SERVICOS DE MANUTENCAO', 'FM2C SERVIÇOS GERAIS', 'G4S INTERATIVA SERVICE',
    'GÁS VANGUARDA SEGURANCA E VIGILANCIA', 'GAP - GESTAO AMBIENTAL & PROJETOS', 'GEOAMBIENTE SOCIEDADE ANONIMA', 'GRI KOLETA - GERENCIAMENTO DE RESÍDUOS INDUSTRIAIS S.A.',
    'IGM SERVIÇOS LOGISTICOS', 'ITSSEG CORRETORA DE SEGUROS S.A.', 'LOSS CONTROL CONSULTORIA E SERVIÇOS', 'LUBRIN LUBRIFICAÇÃO INDUSTRIAL EIRELI', 'LUCIMEIRE PEREIRA DOS SANTOS RODRIGUES - EMPILHADEIRAS',
    'LUIS MARCELO CUNHA BOCHKOVITCH', 'MADINI ASSESSORIA EMPRESARIAL', 'MARCATO ENGENHARIA E COMERCIO', 'MAX-M EMPILHADEIRAS', 'NORDİKA DO BRASIL CONSULTORIA', 'OVERHAUL BRASIL',
    'PLANIT GERENCIAMENTO DE PROJETOS', 'PROMON ENGENHARIA', 'SAFRA COMERCIO DE CAFE IMPORTACAO E EXPORTACAO', 'SATURNO INSTALACOES INDUSTRIAIS LTDA', 'SCR SINALIZAÇÃO E COMERCIO EIRELI',
    'SENIOR SISTEMAS S/A', 'SIMPRESS COMERCIO LOCACAO E SERVICOS', 'SODEXO', 'ULMA PACKAGING', 'UNIPAC'
];
const local_de_armazenamento = [
    'Almoxarifado', 'Armário corta fogo', 'Armário de padrões', 'Armário de padrões internos', 'Armário Laboratório EPAR', 'Armários da áreas de embalagens', 'Calderaria',
    'Casa de tintas', 'Central de gases do LCQ', 'Central de gases do LCQCalderaria', 'Civil', 'Container Lubrin', 'Depósito LCQ no DPA', 'DPA', 'DPA / Apollo',
    'DPA / ApolloLogin', 'Geladeira de inflamáveis', 'Lab. EPAR', 'Laboratórios', 'Lavanderia', 'Login', 'LoginHSILDPASala da Brigada', 'Manutenção', 'Manutenção FM2C',
    'Não utilizado', 'T-2450/52A/52B - area 24', 'T-2503 / T-2506 - area 25A', 'Tancagem', 'TancagemDPA / Apollo', 'TancagemDPA / ApolloLogin', 'TancagemLogin', 'Toller'
];

const ProductEditPage = () => {
    // --- LÓGICA E ESTADOS ---
    const { id } = useParams(); // Pega o ID da URL
    const navigate = useNavigate();
    const { user } = useAuth();

    // Estados para o formulário e controle de UI
    const [productData, setProductData] = useState({
        qtade_maxima_armazenada: '', nome_do_produto: '', fornecedor: '',
        estado_fisico: '', local_de_armazenamento: '', empresa: '',
        perigos_fisicos: [], perigos_saude: [], perigos_meio_ambiente: [],
        palavra_de_perigo: '', categoria: '', status: '', pdf_url: ''
    });
    const [substancias, setSubstancias] = useState([{ nome: '', cas: '', concentracao: '' }]);
    const [selectedFile, setSelectedFile] = useState(null);
    const [loading, setLoading] = useState(true); // Inicia como true para carregar os dados
    const [message, setMessage] = useState('');
    const [showMessage, setShowMessage] = useState(false);
    const [messageType, setMessageType] = useState('success');
    
    // Efeito para buscar os dados do produto ao carregar a página
    useEffect(() => {
        const fetchProduct = async () => {
            try {
                const data = await productService.getProductById(id);
                // Preenche os estados com os dados do produto vindo da API
                setProductData({
                    qtade_maxima_armazenada: data.qtade_maxima_armazenada || '',
                    nome_do_produto: data.nome_do_produto || '',
                    fornecedor: data.fornecedor || '',
                    estado_fisico: data.estado_fisico || '',
                    local_de_armazenamento: data.local_de_armazenamento || '',
                    empresa: data.empresa || '',
                    perigos_fisicos: data.perigos_fisicos || [],
                    perigos_saude: data.perigos_saude || [],
                    perigos_meio_ambiente: data.perigos_meio_ambiente || [],
                    palavra_de_perigo: data.palavra_de_perigo || '',
                    categoria: data.categoria || '',
                    status: data.status || 'pendente',
                    pdf_url: data.pdf_url || ''
                });

                // Se houver substâncias, preenche, senão, mantém uma linha vazia
                if (data.substancias && data.substancias.length > 0) {
                    setSubstancias(data.substancias);
                } else {
                    setSubstancias([{ nome: '', cas: '', concentracao: '' }]);
                }
            } catch (err) {
                setMessage(err.response?.data?.msg || 'Erro ao carregar os dados do produto.');
                setMessageType('error');
                setShowMessage(true);
            } finally {
                setLoading(false);
            }
        };
        fetchProduct();
    }, [id]);

    // Funções de manipulação de formulário (Handlers)
    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setProductData({ ...productData, [name]: value });
    };

    const handleCheckboxChange = (e) => {
        const { name, value, checked } = e.target;
        setProductData((prev) => ({
            ...prev,
            [name]: checked
                ? [...prev[name], value]
                : prev[name].filter((item) => item !== value),
        }));
    };

    const handleSubstanciaChange = (index, event) => {
        const { name, value } = event.target;
        const newSubs = [...substancias];
        newSubs[index][name] = value;
        setSubstancias(newSubs);
    };

    const handleAddSubstancia = () => {
        setSubstancias([...substancias, { nome: '', cas: '', concentracao: '' }]);
    };

    const handleRemoveSubstancia = (index) => {
        const newSubs = substancias.filter((_, i) => i !== index);
        setSubstancias(newSubs);
    };

    const handleFileChange = (e) => {
        setSelectedFile(e.target.files[0]);
    };

    // Função para submeter as alterações
    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setMessage('');
        setShowMessage(false);

        const formData = new FormData();
        // Adiciona o novo arquivo somente se um foi selecionado
        if (selectedFile) {
            formData.append('file', selectedFile);
        }
        
        // Filtra substâncias para não enviar linhas vazias
        const substanciasValidas = substancias.filter(s => s.nome.trim() || s.cas.trim() || s.concentracao.trim());
        const productDataToSend = { ...productData, substancias: substanciasValidas };
        formData.append('productData', JSON.stringify(productDataToSend));

        try {
            await productService.updateProduct(id, formData); // Usa o serviço de ATUALIZAÇÃO
            setMessage('✅ Produto atualizado com sucesso!');
            setMessageType('success');
            setShowMessage(true);
            setTimeout(() => navigate('/app/product-list'), 2000); // Redireciona após o sucesso
        } catch (error) {
            const errorMessage = error.response?.data?.msg || 'Erro ao atualizar o produto.';
            setMessage(errorMessage);
            setMessageType('error');
            setShowMessage(true);
        } finally {
            setLoading(false);
        }
    };

    // Renderização condicional enquanto os dados carregam
    if (loading) {
        return <div className="product-form"><h2>Carregando dados do produto...</h2></div>;
    }

    // --- ESTRUTURA VISUAL (JSX) ---
    return (
        <div className="product-form">
            <h2>Editar Produto</h2>
            <form onSubmit={handleSubmit}>
                {/* Card dados básicos */}
                <div className="card">
                    <div className="form-group">
                        <label htmlFor="nome_do_produto">Nome do Produto:</label>
                        <input id="nome_do_produto" type="text" name="nome_do_produto" value={productData.nome_do_produto} onChange={handleInputChange} />
                    </div>
                    <div className="form-group">
                        <label htmlFor="qtade_maxima_armazenada">Quantidade Máx. Armazenada:</label>
                        <input id="qtade_maxima_armazenada" type="text" name="qtade_maxima_armazenada" value={productData.qtade_maxima_armazenada} onChange={handleInputChange} />
                    </div>
                    <div className="form-group">
                        <label htmlFor="fornecedor">Fornecedor:</label>
                        <input id="fornecedor" type="text" name="fornecedor" value={productData.fornecedor} onChange={handleInputChange} />
                    </div>
                    <div className="form-group">
                        <label htmlFor="empresa">Empresa:</label>
                        <select id="empresa" name="empresa" value={productData.empresa} onChange={handleInputChange}>
                            <option value="">Selecione...</option>
                            {empresas.map((empresa, i) => <option key={i} value={empresa}>{empresa}</option>)}
                        </select>
                    </div>
                    <div className="form-group">
                        <label htmlFor="estado_fisico">Estado Físico:</label>
                        <select id="estado_fisico" name="estado_fisico" value={productData.estado_fisico} onChange={handleInputChange}>
                            <option value="">Selecione...</option>
                            <option value="Líquido">Líquido</option>
                            <option value="Sólido">Sólido</option>
                            <option value="Gasoso">Gasoso</option>
                        </select>
                    </div>
                    <div className="form-group">
                        <label htmlFor="local_de_armazenamento">Local de Armazenamento:</label>
                        <select id="local_de_armazenamento" name="local_de_armazenamento" value={productData.local_de_armazenamento} onChange={handleInputChange}>
                            <option value="">Selecione...</option>
                            {local_de_armazenamento.map((local, i) => <option key={i} value={local}>{local}</option>)}
                        </select>
                    </div>
                    {/* Campo de Status - Apenas Admin pode editar */}
                    <div className="form-group">
                         <label htmlFor="status">Status:</label>
                         <select
                           id="status"
                           name="status"
                           value={productData.status}
                           onChange={handleInputChange}
                           disabled={user?.role !== ROLES.ADMIN} // Desabilitado se não for ADMIN
                         >
                           <option value="pendente">Pendente</option>
                           <option value="aprovado">Aprovado</option>
                           <option value="rejeitado">Rejeitado</option>
                         </select>
                    </div>
                </div>

                {/* Substâncias */}
                <div className="substance-form">
                    <h2>Substâncias</h2>
                    {substancias.map((s, i) => (
                        <div key={i} className="substance-fields">
                            <input type="text" name="nome" placeholder="Substância" value={s.nome} onChange={(e) => handleSubstanciaChange(i, e)} />
                            <input type="text" name="cas" placeholder="Número CAS" value={s.cas} onChange={(e) => handleSubstanciaChange(i, e)} />
                            <input type="text" name="concentracao" placeholder="Concentração (%)" value={s.concentracao} onChange={(e) => handleSubstanciaChange(i, e)} />
                            <button type="button" className="remove-substance-btn" onClick={() => handleRemoveSubstancia(i)}>-</button>
                        </div>
                    ))}
                    <button type="button" className="add-substance-btn" onClick={handleAddSubstancia}>+</button>
                </div>

                {/* Classificação GHS */}
                <div className="card ghs-card">
                    <div className="ghs-header"><h2>Classificação GHS</h2></div>
                    <div className="ghs-container-horizontal">
                        <div className="ghs-group-horizontal">
                            <label>Perigos Físicos</label>
                            <div className="image-checkbox-group">
                                <label><input type="checkbox" name="perigos_fisicos" value="Explosivo" checked={productData.perigos_fisicos.includes("Explosivo")} onChange={handleCheckboxChange} /><div className="image-with-text"><img src={explosivoImg} alt="Explosivo" /><span>Explosivo</span></div></label>
                                <label><input type="checkbox" name="perigos_fisicos" value="Inflamável" checked={productData.perigos_fisicos.includes("Inflamável")} onChange={handleCheckboxChange} /><div className="image-with-text"><img src={inflamavelImg} alt="Inflamável" /><span>Inflamável</span></div></label>
                                <label><input type="checkbox" name="perigos_fisicos" value="Gás sob pressão" checked={productData.perigos_fisicos.includes("Gás sob pressão")} onChange={handleCheckboxChange} /><div className="image-with-text"><img src={gasPressaoImg} alt="Gás sob pressão" /><span>Gás sob pressão</span></div></label>
                                <label><input type="checkbox" name="perigos_fisicos" value="Corrosivo" checked={productData.perigos_fisicos.includes("Corrosivo")} onChange={handleCheckboxChange} /><div className="image-with-text"><img src={corrosivoImg} alt="Corrosivo" /><span>Corrosivo</span></div></label>
                                <label><input type="checkbox" name="perigos_fisicos" value="Oxidante" checked={productData.perigos_fisicos.includes("Oxidante")} onChange={handleCheckboxChange} /><div className="image-with-text"><img src={OxidanteImg} alt="Oxidante" /><span>Oxidante</span></div></label>
                            </div>
                        </div>
                        <div className="ghs-group-horizontal">
                            <label>Perigos à Saúde</label>
                            <div className="image-checkbox-group">
                                <label><input type="checkbox" name="perigos_saude" value="Irritação da Pele" checked={productData.perigos_saude.includes("Irritação da Pele")} onChange={handleCheckboxChange} /><div className="image-with-text"><img src={irritacaoImg} alt="Irritação" /><span>Irritação</span></div></label>
                                <label><input type="checkbox" name="perigos_saude" value="Toxicidade Aguda" checked={productData.perigos_saude.includes("Toxicidade Aguda")} onChange={handleCheckboxChange} /><div className="image-with-text"><img src={MorteImg} alt="Toxicidade" /><span>Toxicidade</span></div></label>
                                <label><input type="checkbox" name="perigos_saude" value="Corrosão da Pele" checked={productData.perigos_saude.includes("Corrosão da Pele")} onChange={handleCheckboxChange} /><div className="image-with-text"><img src={corrosivoImg} alt="Corrosão da Pele" /><span>Corrosivo</span></div></label>
                                <label><input type="checkbox" name="perigos_saude" value="Perigo por Respiração" checked={productData.perigos_saude.includes("Perigo por Respiração")} onChange={handleCheckboxChange} /><div className="image-with-text"><img src={cancerImg} alt="Perigo por Respiração" /><span>Perigo por Respiração</span></div></label>
                            </div>
                        </div>
                        <div className="ghs-group-horizontal">
                            <label>Perigos ao Meio Ambiente</label>
                            <div className="image-checkbox-group">
                                <label><input type="checkbox" name="perigos_meio_ambiente" value="Perigoso para o meio ambiente" checked={productData.perigos_meio_ambiente.includes("Perigoso para o meio ambiente")} onChange={handleCheckboxChange} /><div className="image-with-text"><img src={MeioAmbienteImg} alt="Ambiente" /><span>Meio Ambiente</span></div></label>
                            </div>
                        </div>
                    </div>
                    <div className="ghs-bottom-fields">
                        <label>Palavra de Perigo<input type="text" name="palavra_de_perigo" value={productData.palavra_de_perigo} onChange={handleInputChange} /></label>
                        <label>Categoria<input type="text" name="categoria" value={productData.categoria} onChange={handleInputChange} /></label>
                    </div>
                </div>

                {/* Card para o anexo do arquivo */}
                <div className="card">
                    <h2>Anexar Nova FDS (Opcional)</h2>
                    <p>
                        FDS Atual: {' '}
                        {productData.pdf_url ? 
                            <a href={productData.pdf_url} target="_blank" rel="noopener noreferrer">Visualizar FDS</a>
                            : 'Nenhuma FDS anexada.'}
                    </p>
                    <p>Selecione um novo arquivo abaixo apenas se desejar substituí-lo.</p>
                    <input type="file" accept=".pdf" onChange={handleFileChange} />
                    {selectedFile && <p>Novo arquivo selecionado: {selectedFile.name}</p>}
                </div>

                {/* Botões */}
                <div className="submit-button">
                    <button type="submit" disabled={loading}>{loading ? 'Salvando...' : 'Salvar Alterações'}</button>
                </div>
            </form>

            {/* Mensagem de feedback */}
            {showMessage && (
                <PopupMessage message={message} onClose={() => setShowMessage(false)} type={messageType} />
            )}
        </div>
    );
};

export default ProductEditPage;