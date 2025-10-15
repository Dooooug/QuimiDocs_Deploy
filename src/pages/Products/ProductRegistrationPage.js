//src/pages/Products/ProductRegistrationPage.js
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import productService from '../../services/productService';
import PopupMessage from '../../components/Common/PopupMessage';
import useAuth from '../../hooks/useAuth';
import { ROLES } from '../../utils/constants';

// Importações de imagens (sem alterações)
import explosivoImg from '../../assets/explosivo.png';
import gasPressaoImg from '../../assets/gas_pressao.png';
import inflamavelImg from '../../assets/inflamavel.png';
import corrosivoImg from '../../assets/corrosivo.png';
import irritacaoImg from '../../assets/Irritacao.png';
import cancerImg from '../../assets/cancer.png';
import MeioAmbienteImg from '../../assets/meio_ambiente.png';
import MorteImg from '../../assets/morte.png';
import OxidanteImg from '../../assets/oxidante.png';

// Estilo
import '../../styles/productform.css';

// Listas de dados (sem alterações)
const empresas = [
  'AMARIS DO BRASIL ASSESSORIA EMPRESARIAL', 'AMG - SOLUCOES INDUSTRIAIS', 'BANCO ITAÚ S/A', 'BRAVO SERV. LOG. LTDA - FÁBRICA',
  'CALMITEC CALDEIRARIA E MONTAGENS INDUSTRIAIS', 'CAVALCANTI & ANDRADE ENGENHARIA E CONSULTORIA INDUSTRIAL', 'CONNECTIS TECNOLOGIA DA INFORMAÇÃO E COMUNICAÇÃO DO BRASIL',
  'DATUM K ENGENHARIA', 'ECOSCIENCES - SOLUCOES AMBIENTAIS', 'EMPLOYER ORGANIZAÇÃO DE RECURSOS HUMANOS S.A', 'EMPLOYER RURAL',
  'ENTERPRISE SERVICES BRASIL SERVICOS DE TECNOLOGIA', 'EOLIVEIRA SERVICOS', 'FERNANDO DA SILVA DE OLIVEIRA CONSTRUCOES',
  'FLP CORREA TRANSPORTES', 'FM2C SERVICOS DE MANUTENCAO', 'FM2C SERVIÇOS GERAIS', 'G4S INTERATIVA SERVICE', 'GÁS VANGUARDA SEGURANCA E VIGILANCIA',
  'GAP - GESTAO AMBIENTAL & PROJETOS', 'GEOAMBIENTE SOCIEDADE ANONIMA', 'GRI KOLETA - GERENCIAMENTO DE RESÍDUOS INDUSTRIAIS S.A.',
  'IGM SERVIÇOS LOGISTICOS', 'ITSSEG CORRETORA DE SEGUROS S.A.', 'LOSS CONTROL CONSULTORIA E SERVIÇOS', 'LUBRIN LUBRIFICAÇÃO INDUSTRIAL EIRELI',
  'LUCIMEIRE PEREIRA DOS SANTOS RODRIGUES - EMPILHADEIRAS', 'LUIS MARCELO CUNHA BOCHKOVITCH', 'MADINI ASSESSORIA EMPRESARIAL',
  'MARCATO ENGENHARIA E COMERCIO', 'MAX-M EMPILHADEIRAS', 'NORDİKA DO BRASIL CONSULTORIA', 'OVERHAUL BRASIL', 'PLANIT GERENCIAMENTO DE PROJETOS',
  'PROMON ENGENHARIA', 'SAFRA COMERCIO DE CAFE IMPORTACAO E EXPORTACAO', 'SATURNO INSTALACOES INDUSTRIAIS LTDA', 'SCR SINALIZAÇÃO E COMERCIO EIRELI',
  'SENIOR SISTEMAS S/A', 'SIMPRESS COMERCIO LOCACAO E SERVICOS', 'SODEXO', 'ULMA PACKAGING', 'UNIPAC'
];
const local_de_armazenamento = [
  'Almoxarifado', 'Armário corta fogo', 'Armário de padrões', 'Armário de padrões internos', 'Armário Laboratório EPAR', 'Armários da áreas de embalagens',
  'Calderaria', 'Casa de tintas', 'Central de gases do LCQ', 'Central de gases do LCQCalderaria', 'Civil', 'Container Lubrin', 'Depósito LCQ no DPA', 'DPA',
  'DPA / Apollo', 'DPA / ApolloLogin', 'Geladeira de inflamáveis', 'Lab. EPAR', 'Laboratórios', 'Lavanderia', 'Login', 'LoginHSILDPASala da Brigada',
  'Manutenção', 'Manutenção FM2C', 'Não utilizado', 'T-2450/52A/52B - area 24', 'T-2503 / T-2506 - area 25A', 'Tancagem', 'TancagemDPA / Apollo',
  'TancagemDPA / ApolloLogin', 'TancagemLogin', 'Toller'
];
const unidadesDeEmbalagem = ['Bag(s)', 'Galões','Galão', 'Litro(s)', 'Pacote(s)', 'Peça(s)', 'Unidade(s)','Tonelada(s)','Tambore(s)'];


function isValidCasNumber(casString) {
  if (!/^\d{2,7}-\d{2}-\d$/.test(casString)) return false;
  const digits = casString.replace(/-/g, '');
  const checkDigit = parseInt(digits.slice(-1), 10);
  const casDigitsToCheck = digits.slice(0, -1);
  let totalSum = 0;
  const reversedDigits = casDigitsToCheck.split('').reverse();
  for (let i = 0; i < reversedDigits.length; i++) {
    totalSum += parseInt(reversedDigits[i], 10) * (i + 1);
  }
  return (totalSum % 10) === checkDigit;
}

const ProductRegistrationPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [message, setMessage] = useState('');
  const [showMessage, setShowMessage] = useState(false);
  const [loading, setLoading] = useState(false);
  
  // O estado já está correto, com os campos separados
  const [product, setProduct] = useState({
    quantidade_armazenada: '',
    unidade_embalagem: '',
    nome_do_produto: '', 
    fornecedor: '',
    estado_fisico: '', 
    local_de_armazenamento: '', 
    empresa: '',
    perigos_fisicos: [], 
    perigos_saude: [], 
    perigos_meio_ambiente: [],
    palavra_de_perigo: '', 
    categoria: '',
  });

  const [substancias, setSubstancias] = useState([
    { nome: '', cas: '', concentracao: '', casError: null }
  ]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isFormInvalid, setIsFormInvalid] = useState(true);

  useEffect(() => {
    if (!user || (user.role !== ROLES.ADMIN && user.role !== ROLES.ANALYST)) {
      setMessage('Você não tem permissão para cadastrar produtos.');
      setShowMessage(true);
      setTimeout(() => { navigate('/app/dashboard'); }, 3000);
    }
  }, [user, navigate]);

  useEffect(() => {
    const validateForm = () => {
      const hasRequiredError = !product.nome_do_produto.trim() || !product.fornecedor.trim() || !product.empresa.trim() || !product.estado_fisico.trim() || !product.local_de_armazenamento.trim() || !selectedFile;
      const hasCasError = substancias.some(s => s.casError);
      setIsFormInvalid(hasRequiredError || hasCasError);
    };
    validateForm();
  }, [product, substancias, selectedFile]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setProduct({ ...product, [name]: value });
  };
  const handleCheckboxChange = (e) => {
    const { name, value, checked } = e.target;
    setProduct((prev) => ({
      ...prev,
      [name]: checked ? [...prev[name], value] : prev[name].filter((item) => item !== value),
    }));
  };
  const handleSubstanciaChange = (index, event) => {
    const { name, value } = event.target;
    const newSubs = [...substancias];
    newSubs[index][name] = value;
    if (name === 'cas') {
      if (value.trim() && !isValidCasNumber(value)) {
        newSubs[index].casError = 'Número CAS inválido.';
      } else {
        newSubs[index].casError = null;
      }
    }
    setSubstancias(newSubs);
  };
  const handleAddSubstancia = () => {
    setSubstancias([...substancias, { nome: '', cas: '', concentracao: '', casError: null }]);
  };
  const handleRemoveSubstancia = (index) => {
    const newSubs = substancias.filter((_, i) => i !== index);
    setSubstancias(newSubs);
  };
  const handleFileChange = (e) => {
    setSelectedFile(e.target.files[0]);
  };

  // =============================================================================
  // ✅ ALTERAÇÃO PRINCIPAL: A função handleSubmit foi simplificada.
  // =============================================================================
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (isFormInvalid) {
      setMessage('Verifique os campos obrigatórios e os números CAS antes de enviar.');
      setShowMessage(true);
      return;
    }
    setLoading(true);
    setMessage('');
    setShowMessage(false);
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    // 1. O estado 'product' já possui a estrutura correta que o backend espera.
    //    (com 'quantidade_armazenada' e 'unidade_embalagem' como chaves principais).
    //    Portanto, não precisamos mais criar um objeto aninhado.
    const substanciasValidas = substancias.filter(s => s.nome.trim() || s.cas.trim() || s.concentracao.trim());
    
    const productDataToSend = { 
        ...product, // Copiamos todos os dados do estado
        substancias: substanciasValidas // E adicionamos a lista de substâncias filtrada
    };

    // 2. Enviamos o objeto 'productDataToSend' diretamente.
    formData.append('productData', JSON.stringify(productDataToSend));
    
    try {
      const response = await productService.createProductWithPdf(formData);
      const newProduct = response.product;
      setMessage(`✅ Produto cadastrado com sucesso! Código: ${newProduct.codigo}`);
      setShowMessage(true);
      e.target.reset();
      
      // Resetamos o formulário para o estado inicial correto.
      setProduct({
        quantidade_armazenada: '', unidade_embalagem: '', nome_do_produto: '', fornecedor: '', estado_fisico: '', local_de_armazenamento: '', empresa: '',
        perigos_fisicos: [], perigos_saude: [], perigos_meio_ambiente: [], palavra_de_perigo: '', categoria: '',
      });
      setSubstancias([{ nome: '', cas: '', concentracao: '', casError: null }]);
      setSelectedFile(null);
    } catch (error) {
      console.error('Erro ao adicionar produto:', error);
      const errorMessage = error.response?.data?.msg || 'Erro ao adicionar produto.';
      setMessage(errorMessage);
      setShowMessage(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="product-form">
      <h2>Cadastro de Produtos</h2>
      <form onSubmit={handleSubmit}>
        <div className="card">
          <div className="form-group">
            <label htmlFor="nome_do_produto">Nome do Produto:</label>
            <input id="nome_do_produto" type="text" name="nome_do_produto" value={product.nome_do_produto} onChange={handleInputChange}/>
          </div>
          
          <div className="form-group-split">
            <div className="form-group form-group-quantity"> 
              <label htmlFor="quantidade_armazenada">Quantidade Armazenada:</label>
              <input 
                id="quantidade_armazenada" 
                type="number" 
                name="quantidade_armazenada" 
                value={product.quantidade_armazenada} 
                onChange={handleInputChange}
                placeholder="Ex: 100"
              />
            </div>
            <div className="form-group">
              <label htmlFor="unidade_embalagem">Embalagem:</label>
              <select 
                id="unidade_embalagem" 
                name="unidade_embalagem" 
                value={product.unidade_embalagem} 
                onChange={handleInputChange}
              >
                <option value="">Selecione...</option>
                {unidadesDeEmbalagem.map((unidade, i) => (
                  <option key={i} value={unidade}>{unidade}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="fornecedor">Fornecedor:</label>
            <input id="fornecedor" type="text" name="fornecedor" value={product.fornecedor} onChange={handleInputChange}/>
          </div>
          <div className="form-group">
            <label htmlFor="empresa">Empresa:</label>
            <select id="empresa" name="empresa" value={product.empresa} onChange={handleInputChange}>
              <option value="">Selecione...</option>
              {empresas.map((empresa, i) => <option key={i} value={empresa}>{empresa}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="estado_fisico">Estado Físico:</label>
            <select id="estado_fisico" name="estado_fisico" value={product.estado_fisico} onChange={handleInputChange}>
              <option value="">Selecione...</option>
              <option value="Líquido">Líquido</option>
              <option value="Sólido">Sólido</option>
              <option value="Gasoso">Gasoso</option>
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="local_de_armazenamento">Local de Armazenamento:</label>
            <select id="local_de_armazenamento" name="local_de_armazenamento" value={product.local_de_armazenamento} onChange={handleInputChange}>
              <option value="">Selecione...</option>
              {local_de_armazenamento.map((local, i) => <option key={i} value={local}>{local}</option>)}
            </select>
          </div>
        </div>

        {/* O restante do formulário (substâncias, GHS, etc.) continua igual */}
        <div className="substance-form">
          <h2>Substâncias</h2>
          {substancias.map((s, i) => (
            <div key={i} className="substance-fields">
              <input type="text" name="nome" placeholder="Substância" value={s.nome} onChange={(e) => handleSubstanciaChange(i, e)}/>
              <div className="cas-input-wrapper">
                <input type="text" name="cas" placeholder="Número CAS (ex: 7732-18-5)" value={s.cas} onChange={(e) => handleSubstanciaChange(i, e)} className={s.casError ? 'input-invalid' : ''}/>
                {s.casError && <span className="error-message">{s.casError}</span>}
              </div>
              <input type="text" name="concentracao" placeholder="Concentração (%)" value={s.concentracao} onChange={(e) => handleSubstanciaChange(i, e)}/>
              {substancias.length > 1 && <button type="button" className="remove-substance-btn" onClick={() => handleRemoveSubstancia(i)}>-</button>}
            </div>
          ))}
          <button type="button" className="add-substance-btn" onClick={handleAddSubstancia}>+</button>
        </div>
        
        <div className="card ghs-card">
          <div className="ghs-header"><h2>Classificação GHS</h2></div>
          <div className="ghs-container-horizontal">
            <div className="ghs-group-horizontal">
              <label>Perigos Físicos</label>
              <div className="image-checkbox-group">
                <label><input type="checkbox" name="perigos_fisicos" value="Explosivo" checked={product.perigos_fisicos.includes("Explosivo")} onChange={handleCheckboxChange}/><div className="image-with-text"><img src={explosivoImg} alt="Explosivo"/><span>Explosivo</span></div></label>
                <label><input type="checkbox" name="perigos_fisicos" value="Inflamável" checked={product.perigos_fisicos.includes("Inflamável")} onChange={handleCheckboxChange}/><div className="image-with-text"><img src={inflamavelImg} alt="Inflamável"/><span>Inflamável</span></div></label>
                <label><input type="checkbox" name="perigos_fisicos" value="Gás sob pressão" checked={product.perigos_fisicos.includes("Gás sob pressão")} onChange={handleCheckboxChange}/><div className="image-with-text"><img src={gasPressaoImg} alt="Gás sob pressão"/><span>Gás sob pressão</span></div></label>
                <label><input type="checkbox" name="perigos_fisicos" value="Corrosivo" checked={product.perigos_fisicos.includes("Corrosivo")} onChange={handleCheckboxChange}/><div className="image-with-text"><img src={corrosivoImg} alt="Corrosivo"/><span>Corrosivo</span></div></label>
                <label><input type="checkbox" name="perigos_fisicos" value="Oxidante" checked={product.perigos_fisicos.includes("Oxidante")} onChange={handleCheckboxChange}/><div className="image-with-text"><img src={OxidanteImg} alt="Oxidante"/><span>Oxidante</span></div></label>
              </div>
            </div>
            <div className="ghs-group-horizontal">
              <label>Perigos à Saúde</label>
              <div className="image-checkbox-group">
                <label><input type="checkbox" name="perigos_saude" value="Irritação da Pele" checked={product.perigos_saude.includes("Irritação da Pele")} onChange={handleCheckboxChange}/><div className="image-with-text"><img src={irritacaoImg} alt="Irritação"/><span>Irritação</span></div></label>
                <label><input type="checkbox" name="perigos_saude" value="Toxicidade Aguda" checked={product.perigos_saude.includes("Toxicidade Aguda")} onChange={handleCheckboxChange}/><div className="image-with-text"><img src={MorteImg} alt="Toxicidade"/><span>Toxicidade</span></div></label>
                <label><input type="checkbox" name="perigos_saude" value="Corrosão da Pele" checked={product.perigos_saude.includes("Corrosão da Pele")} onChange={handleCheckboxChange}/><div className="image-with-text"><img src={corrosivoImg} alt="Corrosão da Pele"/><span>Corrosivo</span></div></label>
                <label><input type="checkbox" name="perigos_saude" value="Perigo por Respiração" checked={product.perigos_saude.includes("Perigo por Respiração")} onChange={handleCheckboxChange}/><div className="image-with-text"><img src={cancerImg} alt="Perigo por Respiração"/><span>Perigo por Respiração</span></div></label>
              </div>
            </div>
            <div className="ghs-group-horizontal">
              <label>Perigos ao Meio Ambiente</label>
              <div className="image-checkbox-group">
                <label><input type="checkbox" name="perigos_meio_ambiente" value="Perigoso para o meio ambiente" checked={product.perigos_meio_ambiente.includes("Perigoso para o meio ambiente")} onChange={handleCheckboxChange}/><div className="image-with-text"><img src={MeioAmbienteImg} alt="Ambiente"/><span>Meio Ambiente</span></div></label>
              </div>
            </div>
          </div>
          <div className="ghs-bottom-fields">
            <label>Palavra de Perigo<input type="text" name="palavra_de_perigo" value={product.palavra_de_perigo} onChange={handleInputChange}/></label>
            <label>Categoria<input type="text" name="categoria" value={product.categoria} onChange={handleInputChange}/></label>
          </div>
        </div>

        <div className="card">
          <h2>Anexar FDS (Obrigatório)</h2>
          <input type="file" accept=".pdf" onChange={handleFileChange} required/>
          {selectedFile && <p>Arquivo selecionado: {selectedFile.name}</p>}
        </div>
        
        <div className="submit-button">
          <button type="submit" disabled={loading || isFormInvalid}>
            {loading ? 'Enviando...' : 'Cadastrar Produto com FDS'}
          </button>
        </div>
      </form>

      {showMessage && (
        <PopupMessage
          message={message}
          onClose={() => setShowMessage(false)}
          type={message.includes('sucesso') ? 'success' : 'error'}
        />
      )}
    </div>
  );
};

export default ProductRegistrationPage;